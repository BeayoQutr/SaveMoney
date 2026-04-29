export type PlanResult = {
  remaining_days: number;
  daily_saving: number;
  monthly_available: number;
  daily_available: number;
  target_amount: number;
  feasibility_score: number;
  minimum_living_cost: number;
  safe_saving_capacity: number;
  status: string;
  message: string;
};

export type GeneratePlanPayload = {
  monthly_income: number;
  fixed_expenses: number;
  target_amount: number;
  deadline: string;
  identity: string;
  minimum_living_cost: number;
};

export type AdjustPlanPayload = {
  target_amount: number;
  saved_amount: number;
  remaining_days: number;
  planned_daily_saving: number;
  actual_expense_today: number;
  daily_available: number;
};

export type AdjustResult = {
  remaining_amount: number;
  today_gap: number;
  new_daily_saving: number;
  adjustment_per_day: number;
  status: string;
  message: string;
};

export type ExpenseItem = {
  id: number;
  amount: number;
  note: string;
  date: string;
  category: string;
  payment_method: string | null;
  is_necessary: number | null;
};

export type ExpensePayload = {
  amount: number;
  note: string;
  date: string;
  category?: string;
  payment_method?: string;
  is_necessary?: number;
};

export type ExpenseResult = ExpenseItem & {
  message: string;
};

export type ExpenseListResponse = {
  items: ExpenseItem[];
  total: number;
  limit: number;
  offset: number;
};

export type DailySummary = {
  date: string;
  total_amount: number;
  count: number;
};

export type CategoryItem = {
  category: string;
  total_amount: number;
  count: number;
};

export type CategorySummary = {
  start_date: string;
  end_date: string;
  items: CategoryItem[];
};

export type MonthlySummary = {
  month: string;
  total_amount: number;
  count: number;
  average_daily_amount: number;
  items: CategoryItem[];
};

export type AiMonthlyAdviceResponse = {
  month: string;
  advice: string;
};

export type AiSuggestCategoryResponse = {
  category: string;
  reason: string;
};

export type AiOptimizeNoteResponse = {
  optimized_note: string;
};

export type Preset = {
  monthlyIncome: string;
  fixedExpenses: string;
  minimumLivingCost: string;
  identity: string;
};

export type SavingPlanItem = {
  id: number;
  target_amount: number;
  deadline: string;
  monthly_income: number;
  fixed_expenses: number;
  minimum_living_cost: number;
  identity: string | null;
  saved_amount: number;
  status: string;
};

export type SavingPlanCurrentResponse = {
  plan: SavingPlanItem | null;
  daily_saving: number | null;
  daily_available: number | null;
  remaining_days: number | null;
};
