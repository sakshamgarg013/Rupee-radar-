export type Category =
  | 'Food'
  | 'Travel'
  | 'Shopping'
  | 'Bills'
  | 'EMI'
  | 'Subscriptions'
  | 'Salary'
  | 'Rent'
  | 'Investments'
  | 'Other';

export type TransactionType = 'credit' | 'debit';

export type Frequency = 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'unknown';

export type SessionStatus = 'pending' | 'parsing' | 'processing' | 'ready' | 'failed';

export interface UploadSession {
  id: string;
  session_id?: string | null;
  filename: string;
  file_type: string;
  bank_hint?: string | null;
  status: SessionStatus;
  uploaded_at: string;
  expires_at: string;
  error_message?: string | null;
  row_count?: number | null;
}

export interface Transaction {
  id: number;
  session_id: string;
  date: string;
  description_raw: string;
  description_clean?: string | null;
  amount: number;
  type: TransactionType;
  balance?: number | null;
  category: Category;
  category_confidence: number;
  is_recurring: boolean;
  recurring_group_id?: number | null;
  metadata_json?: string | null;
}

export interface RecurringGroup {
  id: number;
  session_id: string;
  label: string;
  category: string;
  frequency: Frequency;
  typical_amount: number;
  last_seen_date?: string | null;
  confidence: number;
  transaction_ids?: number[];
}

export interface FinancialMetrics {
  total_income: number;
  total_spend: number;
  savings: number;
  savings_rate: number;
  transaction_count: number;
  date_range?: {
    from: string;
    to: string;
  };
}

export interface CategoryBreakdown {
  category: Category;
  total: number;
  percentage: number;
  count: number;
}

export interface BiggestTransaction {
  amount: number;
  description: string;
  date: string;
  category?: string;
}

export interface AnalysisResult {
  session_id: string;
  metrics: FinancialMetrics;
  top_categories: CategoryBreakdown[];
  biggest_transactions: BiggestTransaction[];
  insights: string[];
  generated_at: string;
}

export interface HealthCheckResponse {
  status: string;
  app: string;
  version: string;
  database: string;
}
