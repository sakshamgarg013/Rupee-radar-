import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CATEGORY_ENUMS = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "EMI",
    "Subscriptions",
    "Salary",
    "Rent",
    "Investments",
    "Other",
]


@dataclass
class QuotaUsage:
    requests: int = 0
    tokens: int = 0
    window_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GroqQuotaCoordinator:
    """Shared in-process quota limiter for Groq requests with minute/day budgets."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else Path(__file__).resolve().parents[1] / "groq_quota_state.json"
        self._lock = threading.RLock()
        self._minute_requests: Deque[datetime] = deque()
        self._minute_tokens: Deque[Tuple[datetime, int]] = deque()
        self._daily_usage = self._load_daily_usage()

    def _load_daily_usage(self) -> Dict[str, Any]:
        try:
            if not self.db_path.exists():
                return {"date": datetime.now(timezone.utc).date().isoformat(), "requests": 0, "tokens": 0}
            with self.db_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh) or {}
            today = datetime.now(timezone.utc).date().isoformat()
            if data.get("date") != today:
                return {"date": today, "requests": 0, "tokens": 0}
            return {"date": today, "requests": int(data.get("requests", 0)), "tokens": int(data.get("tokens", 0))}
        except Exception:
            return {"date": datetime.now(timezone.utc).date().isoformat(), "requests": 0, "tokens": 0}

    def _persist_daily_usage(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self.db_path.open("w", encoding="utf-8") as fh:
                json.dump(self._daily_usage, fh)
        except Exception:
            logger.warning("Failed to persist Groq quota usage to disk", exc_info=True)

    def _prune_minute_window(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=60)
        while self._minute_requests and self._minute_requests[0] < cutoff:
            self._minute_requests.popleft()
        while self._minute_tokens and self._minute_tokens[0][0] < cutoff:
            self._minute_tokens.popleft()

    def _refresh_daily_usage(self, now: datetime) -> None:
        if self._daily_usage.get("date") != now.date().isoformat():
            self._daily_usage = {"date": now.date().isoformat(), "requests": 0, "tokens": 0}
            self._persist_daily_usage()

    def reserve(self, estimated_tokens: int = 0, *, request_count: int = 1) -> bool:
        with self._lock:
            now = datetime.now(timezone.utc)
            self._refresh_daily_usage(now)
            self._prune_minute_window(now)

            if len(self._minute_requests) + request_count > settings.GROQ_MAX_RPM:
                return False
            if sum(tokens for _, tokens in self._minute_tokens) + estimated_tokens > settings.GROQ_MAX_TPM:
                return False
            if self._daily_usage["requests"] + request_count > settings.GROQ_MAX_RPD:
                return False
            if self._daily_usage["tokens"] + estimated_tokens > settings.GROQ_MAX_TPD:
                return False

            for _ in range(request_count):
                self._minute_requests.append(now)
            if estimated_tokens > 0:
                self._minute_tokens.append((now, estimated_tokens))
            self._daily_usage["requests"] += request_count
            self._daily_usage["tokens"] += estimated_tokens
            self._persist_daily_usage()
            return True

    def reconcile(
        self,
        reserved_tokens: int = 0,
        *,
        actual_tokens: Optional[int] = None,
        status_ok: bool = True,
        request_count: int = 1,
    ) -> None:
        """Align quota accounting with the actual request outcome."""
        with self._lock:
            now = datetime.now(timezone.utc)
            self._refresh_daily_usage(now)
            if not status_ok:
                for _ in range(request_count):
                    if self._minute_requests:
                        self._minute_requests.pop()
                    if self._minute_tokens:
                        self._minute_tokens.pop()
                self._daily_usage["requests"] = max(0, self._daily_usage["requests"] - request_count)
                self._daily_usage["tokens"] = max(0, self._daily_usage["tokens"] - max(0, reserved_tokens))
                self._persist_daily_usage()
                return

            if actual_tokens is None:
                self._persist_daily_usage()
                return

            if request_count:
                self._daily_usage["tokens"] = max(0, self._daily_usage["tokens"] - max(0, reserved_tokens) + max(0, actual_tokens))
                for _ in range(request_count):
                    if self._minute_tokens:
                        last_ts, _ = self._minute_tokens.pop()
                        self._minute_tokens.append((last_ts, max(0, actual_tokens)))
                        break
            self._persist_daily_usage()

    def get_usage_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            self._refresh_daily_usage(now)
            self._prune_minute_window(now)
            return {
                "rpm": len(self._minute_requests),
                "tpm": sum(tokens for _, tokens in self._minute_tokens),
                "rpd": self._daily_usage["requests"],
                "tpd": self._daily_usage["tokens"],
                "daily_date": self._daily_usage["date"],
            }


quota_coordinator = GroqQuotaCoordinator()


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self._quota = quota_coordinator
        self._last_request_at: Optional[datetime] = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _estimate_tokens(self, payload: str) -> int:
        return max(32, len(payload.split()) * 1.3)

    def _build_category_prompt(self, transactions: List[Dict[str, Any]]) -> str:
        examples = "\n".join([
            '{"id": "tx_1", "category": "Food", "confidence": 0.91}',
            '{"id": "tx_2", "category": "Travel", "confidence": 0.88}',
        ])
        categories = ", ".join(CATEGORY_ENUMS)
        return (
            "You are a financial transaction categorizer for Indian bank statements. "
            "Classify each transaction into one of: " + categories + ". "
            "Use only the cleaned description and amount; omit account numbers, balances, session IDs, or raw bank data. "
            "Return valid JSON only with an array of {id, category, confidence}. "
            "Examples: " + examples + ". "
            "Transactions: " + json.dumps(transactions, ensure_ascii=False)[:4000]
        )

    def _build_insights_prompt(self, metrics: Dict[str, Any]) -> str:
        return (
            "Given this spending summary for an Indian professional, generate 2–3 actionable insights. "
            "Only use the aggregated metrics and real amounts; do not invent hidden data. "
            "Respond with a JSON array of strings. "
            + json.dumps(metrics, ensure_ascii=False)[:4000]
        )

    def categorize_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.is_configured():
            logger.warning("Groq API key is not configured; skipping LLM categorization.")
            return []
        if not transactions:
            return []

        safe_txns = []
        for txn in transactions:
            raw = str(txn.get("description_clean") or txn.get("description_raw") or "").strip()
            if not raw:
                continue
            safe_txns.append({
                "id": txn.get("id") or txn.get("description_clean") or txn.get("description_raw"),
                "description_clean": raw[:120],
                "amount": float(txn.get("amount", 0.0)),
                "type": txn.get("type", "debit"),
            })
        if not safe_txns:
            return []

        estimated_tokens = self._estimate_tokens(self._build_category_prompt(safe_txns))
        if not self._quota.reserve(estimated_tokens):
            logger.info("Groq quota exhausted for categorize_batch; skipping AI categorization.")
            return []

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial transaction categorizer for Indian bank statements."},
                    {"role": "user", "content": self._build_category_prompt(safe_txns)},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=min(256, max(64, estimated_tokens // 2)),
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            results = data.get("results") if isinstance(data, dict) else data
            if not isinstance(results, list):
                raise ValueError("Unexpected Groq response format")
            actual_tokens = getattr(response, "usage", None)
            actual_tokens_count = int(getattr(actual_tokens, "total_tokens", 0) or 0)
            self._quota.reconcile(estimated_tokens, actual_tokens=actual_tokens_count, status_ok=True)
            return [
                {"id": item.get("id"), "category": item.get("category", "Other"), "confidence": float(item.get("confidence", 0.0))}
                for item in results
            ]
        except Exception:
            logger.warning("Groq categorization failed; falling back to deterministic categories.", exc_info=True)
            self._quota.reconcile(estimated_tokens, status_ok=False)
            return []

    def generate_narrative_insights(self, metrics: Dict[str, Any]) -> List[str]:
        if not self.is_configured():
            logger.warning("Groq API key is not configured; skipping narrative insight generation.")
            return []

        estimate = self._estimate_tokens(self._build_insights_prompt(metrics))
        if not self._quota.reserve(estimate):
            logger.info("Groq quota exhausted for generate_narrative_insights; skipping AI insights.")
            return []

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise personal finance assistant for Indian users."},
                    {"role": "user", "content": self._build_insights_prompt(metrics)},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=min(256, max(64, estimate // 2)),
            )
            content = response.choices[0].message.content
            payload = json.loads(content)
            insights = payload.get("insights") if isinstance(payload, dict) else payload
            if not isinstance(insights, list):
                raise ValueError("Unexpected Groq insight response format")
            actual_tokens = getattr(response, "usage", None)
            actual_tokens_count = int(getattr(actual_tokens, "total_tokens", 0) or 0)
            self._quota.reconcile(estimate, actual_tokens=actual_tokens_count, status_ok=True)
            return [str(item).strip() for item in insights if str(item).strip()]
        except Exception:
            logger.warning("Groq narrative insight generation failed; using template insights only.", exc_info=True)
            self._quota.reconcile(estimate, status_ok=False)
            return []
