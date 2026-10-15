import { useState, useEffect, useRef, useMemo, useCallback, createContext, useContext } from "react";
import Auth from "./Auth";
import {
  LayoutDashboard, FileText, Receipt, Users, FolderKanban,
  CreditCard, BarChart3, Bell, Settings, ChevronLeft,
  ChevronRight, Search, Plus, Moon, Sun, LogOut, Sparkles, X,
  TrendingUp, TrendingDown, Clock, CheckCircle, AlertCircle,
  Eye, Send, Download, Trash2, Zap, User, Building2, DollarSign,
  Menu, Home, Briefcase, Inbox
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell
} from "recharts";
import { StoreProvider, useStore, revenueData } from "./store";
import { AddClientModal, CreateQuotationModal, CreateInvoiceModal, RecordPaymentModal, ToastHost } from "./Modals";
import { downloadQuotationPdf, downloadInvoicePdf, downloadReceiptPdf } from "./pdf";
import type { Project } from "./types";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

type Page =
  | "dashboard" | "ai" | "quotations" | "invoices" | "clients"
  | "projects" | "payments" | "analytics" | "notifications" | "settings";

type ModalKind = null | "addClient" | "createQuotation" | "createInvoice" | "recordPayment" | "createProject";

interface ModalState { kind: ModalKind; clientId?: string; invoiceId?: string }
interface ModalOpenOpts { clientId?: string; invoiceId?: string }
interface ModalCtx {
  open: (kind: Exclude<ModalKind, null>, opts?: ModalOpenOpts) => void;
  close: () => void;
}

/* ------------------------------------------------------------------ */
/* Modal context / provider                                            */
/* ------------------------------------------------------------------ */

const ModalContext = createContext<ModalCtx | null>(null);

function useModal() {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error("useModal must be used within ModalProvider");
  return ctx;
}

function ModalProvider({ children }: { children: React.ReactNode }) {
  const [modal, setModal] = useState<ModalState>({ kind: null });

  const open = useCallback((kind: Exclude<ModalKind, null>, opts?: ModalOpenOpts) => {
    setModal({ kind, clientId: opts?.clientId, invoiceId: opts?.invoiceId });
  }, []);
  const close = useCallback(() => setModal({ kind: null }), []);

  const value = useMemo(() => ({ open, close }), [open, close]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [close]);

  return (
    <ModalContext.Provider value={value}>
      {children}
      {modal.kind === "addClient" && <AddClientModal onClose={close} />}
      {modal.kind === "createQuotation" && <CreateQuotationModal onClose={close} clientId={modal.clientId} />}
      {modal.kind === "createInvoice" && <CreateInvoiceModal onClose={close} clientId={modal.clientId} />}
      {modal.kind === "recordPayment" && <RecordPaymentModal onClose={close} invoiceId={modal.invoiceId} />}
      {modal.kind === "createProject" && <CreateProjectModal onClose={close} clientId={modal.clientId} />}
    </ModalContext.Provider>
  );
}

/* ------------------------------------------------------------------ */
/* Create Project modal (was missing entirely)                         */
/* ------------------------------------------------------------------ */

function CreateProjectModal({ onClose, clientId }: { onClose: () => void; clientId?: string }) {
  const { clients, addProject } = useStore();
  const [name, setName] = useState("");
  const [client, setClient] = useState(clientId ?? clients[0]?.id ?? "");
  const [budget, setBudget] = useState("");
  const [deadline, setDeadline] = useState("");
  const [status, setStatus] = useState<Project["status"]>("Planning" as Project["status"]);
  const [error, setError] = useState("");

  const inputCls = "w-full px-3 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return setError("Project name is required.");
    if (!client) return setError("Please select a client.");
    const budgetNum = Number(budget);
    if (!budget || Number.isNaN(budgetNum) || budgetNum < 0) return setError("Enter a valid budget.");
    if (!deadline) return setError("Please choose a deadline.");

    const prettyDeadline = new Date(deadline).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
    addProject({ name: name.trim(), clientId: client, budget: budgetNum, deadline: prettyDeadline, status, progress: 0 } as Omit<Project, "id">);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={onClose}>
      <form
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        className="animate-scale-in w-full max-w-md bg-card border border-border rounded-xl shadow-lg p-6 space-y-4"
      >
        <div className="flex items-center justify-between">
          <h2 className="font-display font-semibold text-lg">New Project</h2>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground"><X size={16} /></button>
        </div>

        <div>
          <label className="text-sm font-medium text-muted-foreground block mb-1.5">Project name</label>
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Restaurant web platform" autoFocus />
        </div>

        <div>
          <label className="text-sm font-medium text-muted-foreground block mb-1.5">Client</label>
          <select className={inputCls} value={client} onChange={(e) => setClient(e.target.value)}>
            {clients.length === 0 && <option value="">No clients yet</option>}
            {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-muted-foreground block mb-1.5">Budget (₹)</label>
            <input className={inputCls} type="number" min={0} value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="75000" />
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground block mb-1.5">Deadline</label>
            <input className={inputCls} type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-muted-foreground block mb-1.5">Status</label>
          <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value as Project["status"])}>
            {["Planning", "On Track", "At Risk", "Delayed", "Completed"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {error && <p className="text-xs text-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors">Cancel</button>
          <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">Create project</button>
        </div>
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Shared UI                                                           */
/* ------------------------------------------------------------------ */

function EmptyState({ icon: Icon, title, body, actionLabel, onAction }: { icon: React.ElementType; title: string; body: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6 bg-card rounded-xl border border-dashed border-border">
      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
        <Icon size={20} className="text-muted-foreground" />
      </div>
      <h3 className="font-display font-semibold text-base">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1.5 max-w-sm">{body}</p>
      {actionLabel && onAction && (
        <button onClick={onAction} className="mt-4 flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={14} /> {actionLabel}
        </button>
      )}
    </div>
  );
}

function fmt(n: number) {
  if (n >= 100000) return `₹${(n / 100000).toFixed(n % 100000 === 0 ? 0 : 1)}L`;
  if (n >= 1000) return `₹${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function fmtFull(n: number) {
  return `₹${n.toLocaleString("en-IN")}`;
}

const STATUS_COLORS: Record<string, string> = {
  Paid: "text-success bg-success/10",
  Sent: "text-primary bg-secondary",
  Viewed: "text-accent bg-accent/10",
  Draft: "text-muted-foreground bg-muted",
  Overdue: "text-danger bg-danger/10",
  Cancelled: "text-muted-foreground bg-muted",
  "Partially Paid": "text-warning bg-warning/10",
  Approved: "text-success bg-success/10",
  Rejected: "text-danger bg-danger/10",
  Expired: "text-muted-foreground bg-muted",
  Planning: "text-primary bg-secondary",
  "On Track": "text-success bg-success/10",
  "At Risk": "text-warning bg-warning/10",
  Delayed: "text-danger bg-danger/10",
  Completed: "text-success bg-success/10",
  Active: "text-success bg-success/10",
  Inactive: "text-muted-foreground bg-muted",
};

function Badge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[status] || "text-muted-foreground bg-muted"}`}>
      {status}
    </span>
  );
}

function Avatar({ initials, color, size = "sm" }: { initials: string; color: string; size?: "sm" | "md" | "lg" }) {
  const sz = size === "sm" ? "w-8 h-8 text-xs" : size === "md" ? "w-10 h-10 text-sm" : "w-12 h-12 text-base";
  return (
    <div className={`${sz} rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0`} style={{ backgroundColor: color }}>
      {initials}
    </div>
  );
}

function KPICard({ title, value, sub, trend, trendUp }: { title: string; value: string; sub?: string; trend?: string; trendUp?: boolean }) {
  return (
    <div className="bg-card rounded-xl p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
      <p className="text-sm text-muted-foreground font-medium">{title}</p>
      <p className="font-display text-2xl font-bold mt-1 tracking-tight">{value}</p>
      {trend && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trendUp ? "text-success" : "text-danger"}`}>
          {trendUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {trend}
        </div>
      )}
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard widgets                                                   */
/* ------------------------------------------------------------------ */

function AIInsightCard({ setPage }: { setPage: (p: Page) => void }) {
  const { invoices, invoiceTotals, clientById } = useStore();
  const overdue = invoices.filter((i) => i.status === "Overdue");
  const outstandingTotal = invoices.reduce((sum, inv) => { const t = invoiceTotals(inv); return sum + Math.max(t.total - inv.amountPaid, 0); }, 0);
  const outstandingClients = new Set(invoices.filter((inv) => { const t = invoiceTotals(inv); return t.total - inv.amountPaid > 0.5; }).map((i) => i.clientId)).size;
  return (
    <div className="ai-border rounded-xl p-5 bg-card border border-border">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
          <Sparkles size={16} className="text-accent" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-accent uppercase tracking-wider">AI Insight</span>
          </div>
          <p className="text-sm text-foreground leading-relaxed">
            Revenue is up <strong>18.4%</strong> this month — strong momentum. However, <strong>₹{outstandingTotal.toLocaleString("en-IN")}</strong> remains outstanding across {outstandingClients} client{outstandingClients === 1 ? "" : "s"}.
            {overdue.length > 0 && <> {overdue[0].id} from {clientById(overdue[0].clientId)?.name} is overdue.</>}
          </p>
          <div className="flex items-center gap-3 mt-3">
            <button onClick={() => setPage("invoices")} className="text-xs font-medium text-primary hover:underline">View invoices</button>
            <span className="text-border">·</span>
            <button onClick={() => setPage("payments")} className="text-xs font-medium text-primary hover:underline">Send reminders</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickActions({ setPage }: { setPage: (p: Page) => void }) {
  const { open } = useModal();
  const actions = [
    { label: "New Quotation", icon: FileText, primary: true, action: () => open("createQuotation") },
    { label: "New Invoice", icon: Receipt, action: () => open("createInvoice") },
    { label: "Add Client", icon: Users, action: () => open("addClient") },
    { label: "New Project", icon: FolderKanban, action: () => open("createProject") },
    { label: "AI Analyzer", icon: Sparkles, ai: true, action: () => setPage("ai") },
    { label: "Record Payment", icon: CreditCard, action: () => open("recordPayment") },
  ];
  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {actions.map((a) => (
        <button
          key={a.label}
          onClick={a.action}
          className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all hover:shadow-md active:scale-95 ${
            a.primary
              ? "bg-primary text-primary-foreground border-primary"
              : a.ai
              ? "bg-accent/10 border-accent/20 text-accent hover:bg-accent/15"
              : "bg-card border-border text-foreground hover:border-primary/40"
          }`}
        >
          <a.icon size={18} />
          <span className="text-xs font-medium text-center leading-tight">{a.label}</span>
        </button>
      ))}
    </div>
  );
}

function RevenueChart({ dark }: { dark: boolean }) {
  const [period, setPeriod] = useState("6M");
  const data = useMemo(() => {
    const months = period === "1M" ? 1 : period === "3M" ? 3 : revenueData.length;
    return revenueData.slice(-months);
  }, [period]);
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="font-display font-semibold text-foreground">Revenue Overview</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Revenue vs expenses</p>
        </div>
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          {["1M", "3M", "6M"].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${period === p ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4338CA" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#4338CA" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#DC2626" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={dark ? "#232844" : "#F1F3F9"} />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: dark ? "#9CA3AF" : "#6B7280" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: dark ? "#9CA3AF" : "#6B7280" }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v / 1000}K`} />
          <Tooltip
            contentStyle={{ background: dark ? "#161928" : "#fff", border: `1px solid ${dark ? "#232844" : "#E5E7EB"}`, borderRadius: 8, fontSize: 12 }}
            formatter={(value: number, name: string) => [fmtFull(value), name === "revenue" ? "Revenue" : "Expenses"]}
          />
          <Area type="monotone" dataKey="revenue" stroke="#4338CA" strokeWidth={2} fill="url(#revGrad)" dot={false} />
          <Area type="monotone" dataKey="expenses" stroke="#DC2626" strokeWidth={1.5} fill="url(#expGrad)" dot={false} strokeDasharray="4 2" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function RecentActivity() {
  const { activities } = useStore();
  const icons: Record<string, React.ReactNode> = {
    payment: <CreditCard size={14} className="text-success" />,
    quotation: <FileText size={14} className="text-primary" />,
    invoice: <Receipt size={14} className="text-primary" />,
    client: <User size={14} className="text-warning" />,
    project: <FolderKanban size={14} className="text-primary" />,
    ai: <Sparkles size={14} className="text-accent" />,
  };
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="font-display font-semibold text-foreground mb-4">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-sm text-muted-foreground">No activity yet. Actions you take will show up here.</p>
      ) : (
        <div className="space-y-4">
          {activities.slice(0, 6).map((a) => (
            <div key={a.id} className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center flex-shrink-0 mt-0.5">
                {icons[a.type]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground leading-snug">{a.message}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{a.time}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ActionRequired({ setPage }: { setPage: (p: Page) => void }) {
  const { invoices, quotations, projects, clientById, invoiceTotals } = useStore();

  const overdue = invoices.filter((i) => i.status === "Overdue");
  const unviewed = quotations.filter((q) => q.status === "Sent");
  const atRiskProjects = projects.filter((p) => p.status === "At Risk" || p.status === "Delayed");
  const outstandingTotal = invoices.reduce((sum, inv) => {
    const t = invoiceTotals(inv);
    return sum + Math.max(t.total - inv.amountPaid, 0);
  }, 0);
  const outstandingClients = new Set(invoices.filter((inv) => { const t = invoiceTotals(inv); return t.total - inv.amountPaid > 0.5; }).map((i) => i.clientId)).size;

  const items: { id: string; icon: React.ElementType; tone: string; text: string; detail: string; cta: string; page: Page }[] = [];
  if (overdue.length > 0) {
    const first = overdue[0];
    const t = invoiceTotals(first);
    items.push({ id: "overdue", icon: AlertCircle, tone: "danger", text: `${overdue.length} invoice${overdue.length > 1 ? "s are" : " is"} overdue`, detail: `${first.id} · ${clientById(first.clientId)?.name ?? ""} · ₹${(t.total - first.amountPaid).toLocaleString("en-IN")}`, cta: "View invoices", page: "invoices" });
  }
  if (unviewed.length > 0) {
    items.push({ id: "unviewed", icon: Eye, tone: "warning", text: `${unviewed.length} quotation${unviewed.length > 1 ? "s haven't" : " hasn't"} been viewed`, detail: unviewed.slice(0, 2).map((q) => q.id).join(", ") + " sent recently", cta: "Review quotations", page: "quotations" });
  }
  if (atRiskProjects.length > 0) {
    const first = atRiskProjects[0];
    items.push({ id: "project", icon: Clock, tone: "warning", text: `${atRiskProjects.length} project deadline${atRiskProjects.length > 1 ? "s are" : " is"} at risk`, detail: `${first.name} · due ${first.deadline}`, cta: "Open project", page: "projects" });
  }
  if (outstandingTotal > 0) {
    items.push({ id: "outstanding", icon: DollarSign, tone: "primary", text: `₹${outstandingTotal.toLocaleString("en-IN")} is outstanding`, detail: `Across ${outstandingClients} client${outstandingClients === 1 ? "" : "s"}`, cta: "Send reminders", page: "payments" });
  }

  const toneClass: Record<string, string> = {
    danger: "text-danger bg-danger/10",
    warning: "text-warning bg-warning/10",
    primary: "text-primary bg-secondary",
  };
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold">Action required</h2>
        <span className="text-xs text-muted-foreground font-medium">{items.length} items</span>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground py-2">Nothing needs your attention right now. Nice work.</p>
      ) : (
        <div className="divide-y divide-border">
          {items.map((it) => {
            const Icon = it.icon;
            return (
              <div key={it.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${toneClass[it.tone]}`}>
                  <Icon size={15} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{it.text}</p>
                  <p className="text-xs text-muted-foreground truncate">{it.detail}</p>
                </div>
                <button onClick={() => setPage(it.page)} className="text-xs font-semibold text-primary hover:underline flex-shrink-0">
                  {it.cta}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function BusinessHealth() {
  const score = 84;
  const breakdown = [
    { label: "Cash flow", value: 88 },
    { label: "Payments", value: 79 },
    { label: "Projects", value: 82 },
    { label: "Clients", value: 91 },
  ];
  const circumference = 2 * Math.PI * 34;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold">Business health</h2>
        <span className="text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">Healthy</span>
      </div>
      <div className="flex items-center gap-5">
        <svg width="84" height="84" viewBox="0 0 84 84" className="flex-shrink-0 -rotate-90">
          <circle cx="42" cy="42" r="34" fill="none" stroke="var(--muted)" strokeWidth="8" />
          <circle
            cx="42" cy="42" r="34" fill="none" stroke="var(--success)" strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          />
          <text x="42" y="49" textAnchor="middle" fontSize="20" fontWeight="700" fill="var(--foreground)" transform="rotate(90 42 42)">
            {score}
          </text>
        </svg>
        <div className="flex-1 space-y-2.5">
          {breakdown.map((b) => (
            <div key={b.label}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-muted-foreground">{b.label}</span>
                <span className="font-medium">{b.value}</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-success" style={{ width: `${b.value}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Dashboard({ dark, setPage }: { dark: boolean; setPage: (p: Page) => void }) {
  const { clients, invoices, projects, invoiceTotals, clientById } = useStore();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const revenueThisMonth = invoices.reduce((sum, inv) => sum + inv.amountPaid, 0);
  const outstandingTotal = invoices.reduce((sum, inv) => { const t = invoiceTotals(inv); return sum + Math.max(t.total - inv.amountPaid, 0); }, 0);
  const outstandingClients = new Set(invoices.filter((inv) => { const t = invoiceTotals(inv); return t.total - inv.amountPaid > 0.5; }).map((i) => i.clientId)).size;
  const activeProjects = projects.filter((p) => p.status !== "Completed" && p.status !== "Cancelled");
  const pastDeadline = projects.filter((p) => p.status === "Delayed").length;
  const expected = invoices.filter((i) => i.status === "Sent" || i.status === "Viewed").reduce((sum, inv) => { const t = invoiceTotals(inv); return sum + (t.total - inv.amountPaid); }, 0);

  const clientRevenue = (id: string) => invoices.filter((i) => i.clientId === id).reduce((s, i) => s + i.amountPaid, 0);
  const topClients = [...clients].sort((a, b) => clientRevenue(b.id) - clientRevenue(a.id)).slice(0, 4);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">{greeting}, Aviral 👋</h1>
        <p className="text-muted-foreground text-sm mt-1">Here's what's happening with your business today.</p>
      </div>

      <AIInsightCard setPage={setPage} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Revenue collected" value={fmtFull(revenueThisMonth)} trend="18.4% vs last month" trendUp />
        <KPICard title="Outstanding" value={fmtFull(outstandingTotal)} sub={`Across ${outstandingClients} client${outstandingClients === 1 ? "" : "s"}`} />
        <KPICard title="Active projects" value={String(activeProjects.length)} sub={pastDeadline > 0 ? `${pastDeadline} past deadline` : "All on schedule"} />
        <KPICard title="Expected" value={fmtFull(expected)} sub="From pending invoices" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ActionRequired setPage={setPage} />
        </div>
        <BusinessHealth />
      </div>

      <div>
        <h2 className="font-display font-semibold text-sm text-muted-foreground uppercase tracking-wider mb-3">Quick Actions</h2>
        <QuickActions setPage={setPage} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RevenueChart dark={dark} />
        </div>
        <RecentActivity />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-semibold">Recent Invoices</h3>
            <button onClick={() => setPage("invoices")} className="text-xs text-primary font-medium hover:underline">View all</button>
          </div>
          {invoices.length === 0 ? (
            <p className="text-sm text-muted-foreground">No invoices yet.</p>
          ) : (
            <div className="space-y-3">
              {invoices.slice(0, 4).map((inv) => {
                const t = invoiceTotals(inv);
                return (
                  <div key={inv.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <div>
                      <p className="text-sm font-medium">{inv.id}</p>
                      <p className="text-xs text-muted-foreground">{clientById(inv.clientId)?.name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <p className="font-mono text-sm font-semibold">{fmt(t.total)}</p>
                      <Badge status={inv.status} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-semibold">Top Clients</h3>
            <button onClick={() => setPage("clients")} className="text-xs text-primary font-medium hover:underline">View all</button>
          </div>
          {topClients.length === 0 ? (
            <p className="text-sm text-muted-foreground">No clients yet.</p>
          ) : (
            <div className="space-y-3">
              {topClients.map((c) => (
                <div key={c.id} className="flex items-center gap-3 py-1.5">
                  <Avatar initials={c.initials} color={c.color} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{c.name}</p>
                    <p className="text-xs text-muted-foreground">{projects.filter((p) => p.clientId === c.id).length} projects</p>
                  </div>
                  <p className="font-mono text-sm font-semibold">{fmt(clientRevenue(c.id))}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* AI Analyzer                                                         */
/* ------------------------------------------------------------------ */

function AIAnalyzer() {
  const { open } = useModal();
  const [input, setInput] = useState("");
  const [analyzed, setAnalyzed] = useState(false);
  const [loading, setLoading] = useState(false);

  const sampleReq = "I need a website for my restaurant with online ordering, table booking and an admin dashboard to manage orders and menu.";

  function analyze() {
    if (!input.trim()) { setInput(sampleReq); return; }
    setLoading(true);
    setAnalyzed(false);
    setTimeout(() => { setLoading(false); setAnalyzed(true); }, 1800);
  }

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
            <Sparkles size={15} className="text-accent" />
          </div>
          <span className="text-xs font-semibold text-accent uppercase tracking-wider">AI Requirement Analyzer</span>
        </div>
        <h1 className="font-display text-2xl font-bold">Turn client requirements into a professional quote.</h1>
        <p className="text-muted-foreground text-sm mt-1">Paste your client's brief and let AI analyze scope, timeline, and pricing.</p>
      </div>

      <div className="ai-border rounded-xl bg-card border border-border p-5">
        <label className="text-sm font-medium text-foreground mb-2 block">Client Requirement</label>
        <textarea
          className="w-full bg-muted rounded-lg p-4 text-sm text-foreground resize-none border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all placeholder:text-muted-foreground"
          rows={5}
          placeholder="Paste or type the client's requirement here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <div className="flex items-center justify-between mt-3">
          <button onClick={() => setInput(sampleReq)} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            Try a sample →
          </button>
          <button
            onClick={analyze}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-accent text-accent-foreground rounded-lg text-sm font-semibold hover:bg-accent/90 transition-all active:scale-95 disabled:opacity-70"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles size={15} />
                Analyze with AI
              </>
            )}
          </button>
        </div>
      </div>

      {analyzed && (
        <div className="space-y-4 animate-fade-in">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Project Type", value: "Restaurant Web Platform" },
              { label: "Timeline", value: "4–6 weeks" },
              { label: "Complexity", value: "Medium" },
              { label: "Category", value: "Web + Mobile" },
            ].map((item) => (
              <div key={item.label} className="bg-card rounded-xl border border-border p-4">
                <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                <p className="font-semibold text-sm">{item.value}</p>
              </div>
            ))}
          </div>

          <div className="bg-card rounded-xl border border-border p-5">
            <h3 className="font-display font-semibold mb-4">Recommended Scope</h3>
            <div className="grid sm:grid-cols-2 gap-2">
              {["Responsive website (desktop + mobile)", "Online ordering system", "Table booking & reservation", "Admin dashboard", "Payment gateway integration", "Menu management CMS", "Order notification system", "Basic analytics & reporting"].map((item) => (
                <div key={item} className="flex items-center gap-2 text-sm">
                  <CheckCircle size={14} className="text-success flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-card rounded-xl border border-border p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-semibold">Suggested Pricing</h3>
              <span className="text-xs text-muted-foreground">Based on market rates</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl font-bold text-primary">₹75,000</span>
              <span className="text-xl text-muted-foreground">–</span>
              <span className="font-display text-3xl font-bold text-primary">₹95,000</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Excluding 18% GST · Advance: 30%</p>
            <div className="flex items-center gap-1 mt-2 text-xs text-accent">
              <Sparkles size={11} />
              <span>AI confidence: High (based on 24 similar projects)</span>
            </div>
            <button
              onClick={() => open("createQuotation")}
              className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 bg-primary text-primary-foreground rounded-lg font-semibold text-sm hover:bg-primary/90 transition-all active:scale-95"
            >
              <FileText size={15} />
              Generate Professional Quotation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Invoices                                                            */
/* ------------------------------------------------------------------ */

const INVOICE_FILTERS = ["All", "Draft", "Sent", "Viewed", "Partially Paid", "Paid", "Overdue", "Cancelled"] as const;

function InvoiceList() {
  const { invoices, clientById, invoiceTotals, setInvoiceStatus } = useStore();
  const { open } = useModal();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<typeof INVOICE_FILTERS[number]>("All");

  const filtered = invoices.filter((inv) => {
    const client = clientById(inv.clientId);
    const s = search.toLowerCase();
    const matchesSearch = !s || inv.id.toLowerCase().includes(s) || (client?.name.toLowerCase().includes(s) ?? false);
    const matchesFilter = filter === "All" || inv.status === filter;
    return matchesSearch && matchesFilter;
  });

  const outstanding = invoices.reduce((sum, inv) => { const t = invoiceTotals(inv); return sum + Math.max(t.total - inv.amountPaid, 0); }, 0);

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Invoices</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{invoices.length} invoices · ₹{outstanding.toLocaleString("en-IN")} outstanding</p>
        </div>
        <button onClick={() => open("createInvoice")} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={15} />
          New Invoice
        </button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            className="w-full pl-9 pr-4 py-2 bg-card border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Search invoices..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {INVOICE_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"}`}
            >
              {f}
            </button>
          ))}
          {filter !== "All" && (
            <button onClick={() => setFilter("All")} className="text-xs text-muted-foreground hover:text-foreground underline ml-1">Clear</button>
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={Receipt}
          title={invoices.length === 0 ? "No invoices yet" : "No invoices match your filters"}
          body={invoices.length === 0 ? "Create your first invoice to start tracking payments." : "Try a different search term or clear your filters."}
          actionLabel={invoices.length === 0 ? "Create Invoice" : undefined}
          onAction={invoices.length === 0 ? () => open("createInvoice") : undefined}
        />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Invoice</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Client</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Amount</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Due</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((inv) => {
                  const client = clientById(inv.clientId);
                  const t = invoiceTotals(inv);
                  return (
                    <tr key={inv.id} className="hover:bg-muted/30 transition-colors group">
                      <td className="px-5 py-4 font-mono font-semibold text-foreground">{inv.id}</td>
                      <td className="px-5 py-4 text-foreground">{client?.name}</td>
                      <td className="px-5 py-4 text-right font-mono font-semibold">{fmtFull(t.total)}</td>
                      <td className="px-5 py-4 text-muted-foreground">{inv.due}</td>
                      <td className="px-5 py-4"><Badge status={inv.status} /></td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                          {inv.status === "Draft" && (
                            <button onClick={() => setInvoiceStatus(inv.id, "Sent")} title="Mark as sent" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"><Send size={14} /></button>
                          )}
                          {inv.status !== "Paid" && inv.status !== "Cancelled" && (
                            <button onClick={() => open("recordPayment", { invoiceId: inv.id })} title="Record payment" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"><CreditCard size={14} /></button>
                          )}
                          <button onClick={() => client && downloadInvoicePdf(inv, client)} title="Download PDF" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"><Download size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Quotations                                                          */
/* ------------------------------------------------------------------ */

const QUOTATION_FILTERS = ["All", "Draft", "Sent", "Viewed", "Approved", "Rejected", "Expired"] as const;

function QuotationList() {
  const { quotations, clientById, quotationTotals, setQuotationStatus, convertQuotationToInvoice, convertQuotationToProject } = useStore();
  const { open } = useModal();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<typeof QUOTATION_FILTERS[number]>("All");

  const filtered = quotations.filter((q) => {
    const client = clientById(q.clientId);
    const s = search.toLowerCase();
    const matchesSearch = !s || q.id.toLowerCase().includes(s) || (client?.name.toLowerCase().includes(s) ?? false) || q.description.toLowerCase().includes(s);
    const matchesFilter = filter === "All" || q.status === filter;
    return matchesSearch && matchesFilter;
  });

  const awaitingApproval = quotations.filter((q) => q.status === "Sent" || q.status === "Viewed").length;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Quotations</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{quotations.length} quotations · {awaitingApproval} awaiting approval</p>
        </div>
        <button onClick={() => open("createQuotation")} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={15} />
          Create Quotation
        </button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            className="w-full pl-9 pr-4 py-2 bg-card border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Search quotations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {QUOTATION_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"}`}
            >
              {f}
            </button>
          ))}
          {filter !== "All" && (
            <button onClick={() => setFilter("All")} className="text-xs text-muted-foreground hover:text-foreground underline ml-1">Clear</button>
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={quotations.length === 0 ? "No quotations yet" : "No quotations match your filters"}
          body={quotations.length === 0 ? "Create your first quotation to start winning business." : "Try a different search term or clear your filters."}
          actionLabel={quotations.length === 0 ? "Create Quotation" : undefined}
          onAction={quotations.length === 0 ? () => open("createQuotation") : undefined}
        />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Quote #</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Client</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Description</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Amount</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Expiry</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((q) => {
                  const client = clientById(q.clientId);
                  const t = quotationTotals(q);
                  return (
                    <tr key={q.id} className="hover:bg-muted/30 transition-colors group">
                      <td className="px-5 py-4 font-mono font-semibold">{q.id}</td>
                      <td className="px-5 py-4">{client?.name}</td>
                      <td className="px-5 py-4 text-muted-foreground max-w-xs truncate">{q.description}</td>
                      <td className="px-5 py-4 text-right font-mono font-semibold">{fmtFull(t.total)}</td>
                      <td className="px-5 py-4 text-muted-foreground">{q.expiry}</td>
                      <td className="px-5 py-4"><Badge status={q.status} /></td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                          {q.status === "Draft" && (
                            <button onClick={() => setQuotationStatus(q.id, "Sent")} title="Send" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><Send size={14} /></button>
                          )}
                          {(q.status === "Sent" || q.status === "Viewed") && (
                            <>
                              <button onClick={() => setQuotationStatus(q.id, "Approved")} title="Approve" className="p-1.5 rounded hover:bg-success/10 text-muted-foreground hover:text-success"><CheckCircle size={14} /></button>
                              <button onClick={() => setQuotationStatus(q.id, "Rejected")} title="Reject" className="p-1.5 rounded hover:bg-danger/10 text-muted-foreground hover:text-danger"><X size={14} /></button>
                            </>
                          )}
                          {q.status === "Approved" && (
                            <>
                              <button onClick={() => convertQuotationToInvoice(q.id)} title="Convert to invoice" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><Receipt size={14} /></button>
                              <button onClick={() => convertQuotationToProject(q.id)} title="Convert to project" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><FolderKanban size={14} /></button>
                            </>
                          )}
                          <button onClick={() => client && downloadQuotationPdf(q, client)} title="Download PDF" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><Download size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Clients                                                             */
/* ------------------------------------------------------------------ */

const CLIENT_FILTERS = ["All", "Active", "Inactive"] as const;

function ClientList() {
  const { clients, invoices, projects, invoiceTotals } = useStore();
  const { open } = useModal();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<typeof CLIENT_FILTERS[number]>("All");

  const clientRevenue = (id: string) => invoices.filter((i) => i.clientId === id).reduce((s, i) => s + i.amountPaid, 0);
  const clientOutstanding = (id: string) => invoices.filter((i) => i.clientId === id).reduce((s, i) => { const t = invoiceTotals(i); return s + Math.max(t.total - i.amountPaid, 0); }, 0);
  const clientProjectCount = (id: string) => projects.filter((p) => p.clientId === id).length;

  const filtered = clients.filter((c) => {
    const s = search.toLowerCase();
    const matchesSearch = !s || c.name.toLowerCase().includes(s) || c.contact.toLowerCase().includes(s);
    const matchesFilter = filter === "All" || c.status === filter;
    return matchesSearch && matchesFilter;
  });

  const totalRevenue = clients.reduce((s, c) => s + clientRevenue(c.id), 0);

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Clients</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{clients.length} clients · ₹{totalRevenue.toLocaleString("en-IN")} total revenue</p>
        </div>
        <button onClick={() => open("addClient")} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={15} />
          Add Client
        </button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative max-w-xs flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            className="w-full pl-9 pr-4 py-2 bg-card border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            placeholder="Search clients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5">
          {CLIENT_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={Users}
          title={clients.length === 0 ? "No clients yet" : "No clients match your search"}
          body={clients.length === 0 ? "Add your first client to start tracking quotations, projects and payments." : "Try a different search term or filter."}
          actionLabel={clients.length === 0 ? "Add Client" : undefined}
          onAction={clients.length === 0 ? () => open("addClient") : undefined}
        />
      ) : (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((c) => {
            const outstanding = clientOutstanding(c.id);
            return (
              <div key={c.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Avatar initials={c.initials} color={c.color} size="md" />
                    <div>
                      <p className="font-semibold text-foreground leading-tight">{c.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{c.contact}</p>
                    </div>
                  </div>
                  <Badge status={c.status} />
                </div>
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">Total Revenue</p>
                    <p className="font-mono font-semibold text-sm mt-0.5">{fmtFull(clientRevenue(c.id))}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Outstanding</p>
                    <p className={`font-mono font-semibold text-sm mt-0.5 ${outstanding > 0 ? "text-danger" : "text-success"}`}>
                      {outstanding > 0 ? fmtFull(outstanding) : "₹0"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Projects</p>
                    <p className="font-semibold text-sm mt-0.5">{clientProjectCount(c.id)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Last contact</p>
                    <p className="text-sm mt-0.5">{c.lastContact}</p>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">GSTIN: <span className="font-mono text-foreground">{c.gstin || "—"}</span></p>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                    <button onClick={() => open("createQuotation", { clientId: c.id })} title="New quotation" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><FileText size={13} /></button>
                    <button onClick={() => open("createInvoice", { clientId: c.id })} title="New invoice" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><Receipt size={13} /></button>
                    <button onClick={() => open("createProject", { clientId: c.id })} title="New project" className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"><FolderKanban size={13} /></button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Projects                                                            */
/* ------------------------------------------------------------------ */

const PROJECT_FILTERS = ["All", "Planning", "On Track", "At Risk", "Delayed", "Completed"] as const;

function ProjectList() {
  const { projects, clientById } = useStore();
  const { open } = useModal();
  const [filter, setFilter] = useState<typeof PROJECT_FILTERS[number]>("All");
  const healthColor = (s: string) =>
    s === "On Track" ? "text-success" : s === "At Risk" ? "text-warning" : s === "Delayed" ? "text-danger" : s === "Planning" ? "text-primary" : "text-muted-foreground";
  const healthBg = (s: string) =>
    s === "On Track" ? "bg-success" : s === "At Risk" ? "bg-warning" : s === "Delayed" ? "bg-danger" : s === "Planning" ? "bg-primary" : "bg-muted-foreground";

  const filtered = filter === "All" ? projects : projects.filter((p) => p.status === filter);
  const pastDeadline = projects.filter((p) => p.status === "Delayed").length;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Projects</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{projects.length} projects{pastDeadline > 0 ? ` · ${pastDeadline} past deadline` : ""}</p>
        </div>
        <button onClick={() => open("createProject")} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={15} />
          New Project
        </button>
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        {PROJECT_FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"}`}
          >
            {f}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title={projects.length === 0 ? "No projects yet" : "No projects match this filter"}
          body={projects.length === 0 ? "Create a project to track scope, budget and delivery." : "Try a different filter."}
          actionLabel={projects.length === 0 ? "New Project" : undefined}
          onAction={projects.length === 0 ? () => open("createProject") : undefined}
        />
      ) : (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((p) => (
            <div key={p.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0 pr-3">
                  <p className="font-semibold text-foreground leading-tight">{p.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{clientById(p.clientId)?.name}</p>
                </div>
                <span className={`text-xs font-semibold flex-shrink-0 ${healthColor(p.status)}`}>{p.status}</span>
              </div>

              <div className="mb-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-muted-foreground">Progress</span>
                  <span className="text-xs font-semibold">{p.progress}%</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${healthBg(p.status)}`} style={{ width: `${p.progress}%` }} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Budget</p>
                  <p className="font-mono font-semibold mt-0.5">{fmt(p.budget)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Deadline</p>
                  <p className="mt-0.5">{p.deadline}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Payments                                                            */
/* ------------------------------------------------------------------ */

function PaymentsPage() {
  const { payments, invoices, clientById, invoiceTotals } = useStore();
  const { open } = useModal();

  const collected = payments.reduce((s, p) => s + p.amount, 0);
  const pending = invoices.reduce((s, inv) => { const t = invoiceTotals(inv); return s + Math.max(t.total - inv.amountPaid, 0); }, 0);
  const overdueInvoices = invoices.filter((i) => i.status === "Overdue");
  const overdueAmount = overdueInvoices.reduce((s, inv) => { const t = invoiceTotals(inv); return s + Math.max(t.total - inv.amountPaid, 0); }, 0);
  const pendingCount = invoices.filter((i) => i.status !== "Paid" && i.status !== "Cancelled").length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Payments</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Track collections, pending dues, and payment history.</p>
        </div>
        <button onClick={() => open("recordPayment")} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all active:scale-95">
          <Plus size={15} />
          Record Payment
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Collected" value={fmtFull(collected)} />
        <KPICard title="Pending" value={fmtFull(pending)} sub={`${pendingCount} invoice${pendingCount === 1 ? "" : "s"}`} />
        <KPICard title="Overdue" value={fmtFull(overdueAmount)} sub={`${overdueInvoices.length} invoice${overdueInvoices.length === 1 ? "" : "s"}`} />
        <KPICard title="Total transactions" value={String(payments.length)} />
      </div>

      {payments.length === 0 ? (
        <EmptyState icon={CreditCard} title="No payments recorded yet" body="Record your first payment to keep invoices and cash flow up to date." actionLabel="Record Payment" onAction={() => open("recordPayment")} />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <h3 className="font-display font-semibold">Recent Transactions</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Payment ID</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Invoice</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Client</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Amount</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Date</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Method</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {payments.map((p) => {
                  const invoice = invoices.find((i) => i.id === p.invoiceId);
                  const client = clientById(p.clientId);
                  return (
                    <tr key={p.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-5 py-4 font-mono font-semibold text-xs">{p.id}</td>
                      <td className="px-5 py-4 font-mono text-primary text-xs">{p.invoiceId}</td>
                      <td className="px-5 py-4">{client?.name}</td>
                      <td className="px-5 py-4 text-right font-mono font-semibold">{fmtFull(p.amount)}</td>
                      <td className="px-5 py-4 text-muted-foreground">{p.date}</td>
                      <td className="px-5 py-4">
                        <span className="px-2 py-0.5 bg-secondary text-secondary-foreground rounded text-xs font-medium">{p.method}</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => invoice && client && downloadReceiptPdf(p, invoice, client)}
                          disabled={!invoice || !client}
                          className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground inline-flex disabled:opacity-40"
                          title="Download receipt"
                        >
                          <Download size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Analytics                                                           */
/* ------------------------------------------------------------------ */

function AnalyticsPage({ dark }: { dark: boolean }) {
  const { clients, invoices, quotations, payments, invoiceTotals } = useStore();
  const [period, setPeriod] = useState("6M");

  const chartData = useMemo(() => {
    const months = period === "1M" ? 1 : period === "3M" ? 3 : period === "6M" ? 6 : revenueData.length;
    return revenueData.slice(-months);
  }, [period]);

  const methodTotals: Record<string, number> = {};
  payments.forEach((p) => { methodTotals[p.method] = (methodTotals[p.method] || 0) + p.amount; });
  const methodColors: Record<string, string> = { UPI: "#7C3AED", "Bank Transfer": "#059669", Card: "#4338CA", Cash: "#D97706", Other: "#0891B2" };
  const paymentMethods = Object.entries(methodTotals).map(([name, value]) => ({ name, value, color: methodColors[name] || "#6B7280" }));

  const totalRevenue = invoices.reduce((s, i) => s + i.amountPaid, 0);
  const totalBilled = invoices.reduce((s, i) => s + invoiceTotals(i).total, 0);
  const collectionRate = totalBilled > 0 ? Math.round((totalRevenue / totalBilled) * 100) : 0;
  const approvedQuotes = quotations.filter((q) => q.status === "Approved").length;
  const decidedQuotes = quotations.filter((q) => q.status === "Approved" || q.status === "Rejected");
  const conversionRate = decidedQuotes.length > 0 ? Math.round((approvedQuotes / decidedQuotes.length) * 100) : 0;
  const avgInvoice = invoices.length > 0 ? totalBilled / invoices.length : 0;
  const clientRevenue = (id: string) => invoices.filter((i) => i.clientId === id).reduce((s, i) => s + i.amountPaid, 0);
  const maxClientRevenue = Math.max(...clients.map((c) => clientRevenue(c.id)), 1);
  const topClients = [...clients].sort((a, b) => clientRevenue(b.id) - clientRevenue(a.id)).slice(0, 5);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Your business performance at a glance.</p>
        </div>
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          {["1M", "3M", "6M", "1Y"].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${period === p ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total revenue collected" value={fmtFull(totalRevenue)} />
        <KPICard title="Collection rate" value={`${collectionRate}%`} sub="Paid vs total billed" />
        <KPICard title="Quote conversion" value={`${conversionRate}%`} sub={`${approvedQuotes} of ${decidedQuotes.length} decided quotes approved`} />
        <KPICard title="Avg invoice value" value={fmtFull(Math.round(avgInvoice))} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-card rounded-xl border border-border p-5">
          <h3 className="font-display font-semibold mb-4">Revenue & Expenses</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke={dark ? "#232844" : "#F1F3F9"} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: dark ? "#9CA3AF" : "#6B7280" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: dark ? "#9CA3AF" : "#6B7280" }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v / 1000}K`} />
              <Tooltip
                contentStyle={{ background: dark ? "#161928" : "#fff", border: `1px solid ${dark ? "#232844" : "#E5E7EB"}`, borderRadius: 8, fontSize: 12 }}
                formatter={(value: number, name: string) => [fmtFull(value), name === "revenue" ? "Revenue" : name === "expenses" ? "Expenses" : "Profit"]}
              />
              <Bar dataKey="revenue" fill="#4338CA" radius={[4, 4, 0, 0]} />
              <Bar dataKey="expenses" fill={dark ? "#374151" : "#E5E7EB"} radius={[4, 4, 0, 0]} />
              <Bar dataKey="profit" fill="#059669" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="font-display font-semibold mb-4">Payment Methods</h3>
          {paymentMethods.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No payments recorded yet.</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={paymentMethods} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                    {paymentMethods.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => fmtFull(v)} contentStyle={{ background: dark ? "#161928" : "#fff", border: `1px solid ${dark ? "#232844" : "#E5E7EB"}`, borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {paymentMethods.map((m) => (
                  <div key={m.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: m.color }} />
                      <span className="text-muted-foreground">{m.name}</span>
                    </div>
                    <span className="font-mono font-semibold">{fmt(m.value)}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-5">
        <h3 className="font-display font-semibold mb-4">Top Clients by Revenue</h3>
        {topClients.length === 0 ? (
          <p className="text-sm text-muted-foreground">No clients yet.</p>
        ) : (
          <div className="space-y-4">
            {topClients.map((c, i) => (
              <div key={c.id} className="flex items-center gap-4">
                <span className="text-xs text-muted-foreground w-4 font-mono">{i + 1}</span>
                <Avatar initials={c.initials} color={c.color} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium truncate">{c.name}</span>
                    <span className="font-mono text-sm font-semibold ml-4">{fmtFull(clientRevenue(c.id))}</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(clientRevenue(c.id) / maxClientRevenue) * 100}%`, backgroundColor: c.color }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Notifications                                                       */
/* ------------------------------------------------------------------ */

function NotificationsPage({ setPage }: { setPage: (p: Page) => void }) {
  const { notifications, markNotificationRead, markAllNotificationsRead, deleteNotification } = useStore();
  const [filter, setFilter] = useState("All");
  const categories = ["All", "Payments", "Clients", "Projects", "AI", "System", "Quotations", "Invoices"];
  const filtered = filter === "All" ? notifications : notifications.filter((n) => n.category === filter);
  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="max-w-2xl space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Notifications</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{unreadCount} unread</p>
        </div>
        {unreadCount > 0 && <button onClick={markAllNotificationsRead} className="text-sm text-primary font-medium hover:underline">Mark all read</button>}
      </div>

      <div className="flex gap-2 flex-wrap">
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === c ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"}`}
          >
            {c}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Inbox} title="No notifications" body="You're all caught up. New activity will show up here." />
      ) : (
        <div className="space-y-2">
          {filtered.map((n) => (
            <div
              key={n.id}
              onClick={() => { markNotificationRead(n.id); if (n.relatedPage) setPage(n.relatedPage as Page); }}
              className={`flex items-start gap-4 p-4 rounded-xl border transition-colors cursor-pointer hover:border-primary/30 group ${n.read ? "bg-card border-border" : "bg-card border-primary/20 shadow-sm"}`}
            >
              <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center text-base flex-shrink-0">
                {n.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">{n.title}</p>
                  {!n.read && <div className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />}
                </div>
                <p className="text-sm text-muted-foreground mt-0.5 leading-snug">{n.body}</p>
                <p className="text-xs text-muted-foreground/60 mt-1.5">{n.time}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); deleteNotification(n.id); }}
                className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-danger opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity flex-shrink-0"
                aria-label="Delete notification"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Settings                                                            */
/* ------------------------------------------------------------------ */

function SettingsPage() {
  const sections = ["Profile", "Business", "Branding", "Invoice Settings", "GST & Taxes", "Payments", "Notifications", "Security", "Integrations", "AI Preferences", "Billing", "Team"];
  const [active, setActive] = useState("Profile");
  const inputCls = "w-full px-3 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all";

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-2xl font-bold mb-6">Settings</h1>
      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0 hidden sm:block">
          <nav className="space-y-0.5">
            {sections.map((s) => (
              <button
                key={s}
                onClick={() => setActive(s)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${active === s ? "bg-secondary text-primary font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}
              >
                {s}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 min-w-0 bg-card rounded-xl border border-border p-6">
          <div className="sm:hidden mb-4">
            <select className={inputCls} value={active} onChange={(e) => setActive(e.target.value)}>
              {sections.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <h2 className="font-display font-semibold text-lg mb-5">{active}</h2>
          {active === "Profile" && (
            <div className="space-y-5 max-w-lg">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xl font-bold font-display">A</div>
                <button className="px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors">Change photo</button>
              </div>
              {[["Full name", "Aviral Sharma"], ["Email", "aviral@example.com"], ["Phone", "+91 98765 43210"]].map(([label, val]) => (
                <div key={label}>
                  <label className="text-sm font-medium text-muted-foreground block mb-1.5">{label}</label>
                  <input defaultValue={val} className={inputCls} />
                </div>
              ))}
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all">Save changes</button>
            </div>
          )}
          {active === "Business" && (
            <div className="space-y-5 max-w-lg">
              {[["Business name", "Aviral Studio"], ["GSTIN", "27AAPCS1234A1Z5"], ["PAN", "AAPCS1234A"], ["Address", "Mumbai, Maharashtra"]].map(([label, val]) => (
                <div key={label}>
                  <label className="text-sm font-medium text-muted-foreground block mb-1.5">{label}</label>
                  <input defaultValue={val} className={inputCls} />
                </div>
              ))}
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 transition-all">Save</button>
            </div>
          )}
          {active !== "Profile" && active !== "Business" && (
            <p className="text-muted-foreground text-sm">Configure your {active.toLowerCase()} preferences here.</p>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Command palette (with working keyboard navigation)                  */
/* ------------------------------------------------------------------ */

interface PaletteItem { key: string; group: string; label: string; icon: React.ElementType; action: () => void }

function CommandPalette({ onClose, setPage }: { onClose: () => void; setPage: (p: Page) => void }) {
  const { clients, invoices, quotations, projects, clientById } = useStore();
  const { open } = useModal();
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { setActiveIdx(0); }, [query]);

  const go = useCallback((p: Page) => { setPage(p); onClose(); }, [setPage, onClose]);
  const openModal = useCallback((k: Exclude<ModalKind, null>) => { open(k); onClose(); }, [open, onClose]);

  const items: PaletteItem[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    const commands: PaletteItem[] = [
      { key: "c-dash", group: "Commands", label: "Go to Dashboard", icon: LayoutDashboard, action: () => go("dashboard") },
      { key: "c-ai", group: "Commands", label: "Go to AI Analyzer", icon: Sparkles, action: () => go("ai") },
      { key: "c-quo", group: "Commands", label: "Go to Quotations", icon: FileText, action: () => go("quotations") },
      { key: "c-inv", group: "Commands", label: "Go to Invoices", icon: Receipt, action: () => go("invoices") },
      { key: "c-cli", group: "Commands", label: "Go to Clients", icon: Users, action: () => go("clients") },
      { key: "c-pro", group: "Commands", label: "Go to Projects", icon: FolderKanban, action: () => go("projects") },
      { key: "c-pay", group: "Commands", label: "Go to Payments", icon: CreditCard, action: () => go("payments") },
      { key: "c-ana", group: "Commands", label: "Go to Analytics", icon: BarChart3, action: () => go("analytics") },
      { key: "c-notif", group: "Commands", label: "Go to Notifications", icon: Bell, action: () => go("notifications") },
      { key: "c-set", group: "Commands", label: "Go to Settings", icon: Settings, action: () => go("settings") },
      { key: "c-nq", group: "Commands", label: "Create quotation", icon: Plus, action: () => openModal("createQuotation") },
      { key: "c-ni", group: "Commands", label: "Create invoice", icon: Plus, action: () => openModal("createInvoice") },
      { key: "c-nc", group: "Commands", label: "Add client", icon: Plus, action: () => openModal("addClient") },
      { key: "c-np", group: "Commands", label: "New project", icon: Plus, action: () => openModal("createProject") },
      { key: "c-rp", group: "Commands", label: "Record payment", icon: Plus, action: () => openModal("recordPayment") },
    ];
    if (!q) return commands;

    const matchedClients: PaletteItem[] = clients
      .filter((c) => c.name.toLowerCase().includes(q) || c.contact.toLowerCase().includes(q))
      .slice(0, 4)
      .map((c) => ({ key: `cl-${c.id}`, group: "Clients", label: c.name, icon: Users, action: () => go("clients") }));
    const matchedQuotations: PaletteItem[] = quotations
      .filter((qt) => qt.id.toLowerCase().includes(q) || qt.description.toLowerCase().includes(q) || (clientById(qt.clientId)?.name.toLowerCase().includes(q) ?? false))
      .slice(0, 4)
      .map((qt) => ({ key: `q-${qt.id}`, group: "Quotations", label: `${qt.id} — ${qt.description}`, icon: FileText, action: () => go("quotations") }));
    const matchedInvoices: PaletteItem[] = invoices
      .filter((i) => i.id.toLowerCase().includes(q) || (clientById(i.clientId)?.name.toLowerCase().includes(q) ?? false))
      .slice(0, 4)
      .map((i) => ({ key: `i-${i.id}`, group: "Invoices", label: `${i.id} — ${clientById(i.clientId)?.name ?? ""}`, icon: Receipt, action: () => go("invoices") }));
    const matchedProjects: PaletteItem[] = projects
      .filter((p) => p.name.toLowerCase().includes(q))
      .slice(0, 4)
      .map((p) => ({ key: `p-${p.id}`, group: "Projects", label: p.name, icon: FolderKanban, action: () => go("projects") }));
    const filteredCommands = commands.filter((c) => c.label.toLowerCase().includes(q));

    return [...matchedClients, ...matchedQuotations, ...matchedInvoices, ...matchedProjects, ...filteredCommands];
  }, [query, clients, quotations, invoices, projects, clientById, go, openModal]);

  const groups = useMemo(() => {
    const order = ["Clients", "Quotations", "Invoices", "Projects", "Commands"];
    return order.map((g) => ({ title: g, items: items.filter((it) => it.group === g) })).filter((g) => g.items.length > 0);
  }, [items]);

  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-idx="${activeIdx}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIdx]);

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx((i) => (items.length ? (i + 1) % items.length : 0)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx((i) => (items.length ? (i - 1 + items.length) % items.length : 0)); }
    else if (e.key === "Enter") { e.preventDefault(); items[activeIdx]?.action(); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/30" onClick={onClose}>
      <div className="animate-scale-in bg-card border border-border rounded-xl shadow-lg w-full max-w-lg overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-border">
          <Search size={16} className="text-muted-foreground" />
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            placeholder="Search commands, clients, invoices..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <kbd className="text-xs text-muted-foreground px-1.5 py-0.5 bg-muted rounded border border-border">Esc</kbd>
        </div>
        <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
          {groups.map((g) => (
            <div key={g.title} className="mb-1">
              <p className="px-3 pt-2 pb-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{g.title}</p>
              {g.items.map((it) => {
                const idx = items.indexOf(it);
                const Icon = it.icon;
                return (
                  <button
                    key={it.key}
                    data-idx={idx}
                    onClick={it.action}
                    onMouseEnter={() => setActiveIdx(idx)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-foreground transition-colors text-left ${idx === activeIdx ? "bg-muted" : "hover:bg-muted"}`}
                  >
                    <Icon size={15} className="text-muted-foreground flex-shrink-0" />
                    <span className="truncate">{it.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
          {items.length === 0 && (
            <p className="text-center text-sm text-muted-foreground py-6">No results found</p>
          )}
        </div>
        <div className="px-4 py-2 border-t border-border">
          <p className="text-xs text-muted-foreground">↑↓ Navigate · Enter Select · Esc Close</p>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Navigation config                                                   */
/* ------------------------------------------------------------------ */

interface NavItem { id: Page; label: string; icon: React.ElementType; ai?: boolean }

const navItems: NavItem[] = [
  { id: "dashboard", label: "Overview", icon: LayoutDashboard },
  { id: "ai", label: "AI Workspace", icon: Sparkles, ai: true },
  { id: "quotations", label: "Quotations", icon: FileText },
  { id: "invoices", label: "Invoices", icon: Receipt },
  { id: "clients", label: "Clients", icon: Users },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "payments", label: "Payments", icon: CreditCard },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
];

const bottomNavItems: NavItem[] = [
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "settings", label: "Settings", icon: Settings },
];

const mobileNavItems: NavItem[] = [
  { id: "dashboard", label: "Home", icon: Home },
  { id: "clients", label: "Clients", icon: Users },
  { id: "invoices", label: "Invoices", icon: Receipt },
  { id: "projects", label: "Projects", icon: Briefcase },
  { id: "notifications", label: "More", icon: Bell },
];

/* ------------------------------------------------------------------ */
/* Shell (needs store + modal providers)                               */
/* ------------------------------------------------------------------ */

function Shell({ onSignOut }: { onSignOut: () => void }) {
  const { notifications, markNotificationRead } = useStore();
  const [page, setPage] = useState<Page>("dashboard");
  const [dark, setDark] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const saved = window.localStorage.getItem("rexipt-theme");
    if (saved) return saved === "dark";
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });
  const [collapsed, setCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    window.localStorage.setItem("rexipt-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
      if (e.key === "Escape") {
        setCmdOpen(false);
        setNotifOpen(false);
        setProfileOpen(false);
        setMobileNavOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const unread = notifications.filter((n) => !n.read).length;

  const navigate = (p: Page) => {
    setPage(p);
    setNotifOpen(false);
    setProfileOpen(false);
    setMobileNavOpen(false);
  };

  const Logo = () => (
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
        <Receipt size={16} className="text-primary-foreground" />
      </div>
      <div>
        <p className="font-display font-bold text-sm leading-none">REXIPT</p>
        <p className="font-display font-bold text-sm leading-none text-primary">MAKER</p>
      </div>
    </div>
  );

  const navBtnClass = (item: NavItem) => {
    const active = page === item.id;
    if (active) return item.ai ? "bg-accent/10 text-accent" : "bg-secondary text-primary";
    return "text-muted-foreground hover:text-foreground hover:bg-muted";
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className={`hidden md:flex flex-col flex-shrink-0 border-r border-border bg-card transition-all duration-300 ${collapsed ? "w-16" : "w-60"}`}>
        <div className={`flex items-center px-4 py-5 border-b border-border ${collapsed ? "justify-center" : ""}`}>
          {collapsed ? (
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
              <Receipt size={16} className="text-primary-foreground" />
            </div>
          ) : <Logo />}
        </div>

        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${navBtnClass(item)} ${collapsed ? "justify-center" : ""}`}
            >
              <item.icon size={17} className="flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && item.ai && (
                <span className="ml-auto text-[10px] font-bold bg-accent/10 text-accent px-1.5 py-0.5 rounded-full">AI</span>
              )}
            </button>
          ))}

          <div className="my-2 border-t border-border" />

          {bottomNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${navBtnClass(item)} ${collapsed ? "justify-center" : ""}`}
            >
              <item.icon size={17} className="flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && item.id === "notifications" && unread > 0 && (
                <span className="ml-auto w-5 h-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center">{unread}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="p-2 border-t border-border">
          <button
            onClick={() => setCollapsed((v) => !v)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors ${collapsed ? "justify-center" : ""}`}
          >
            {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span>Collapse</span></>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        <header className="flex items-center gap-4 px-4 md:px-6 py-3.5 border-b border-border bg-card flex-shrink-0">
          <button className="md:hidden p-1.5 rounded-lg hover:bg-muted transition-colors" onClick={() => setMobileNavOpen(true)} aria-label="Open menu">
            <Menu size={18} />
          </button>

          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center gap-2 px-3 py-2 bg-muted border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors flex-1 max-w-sm"
          >
            <Search size={14} />
            <span className="flex-1 text-left hidden sm:block">Search anything...</span>
            <kbd className="hidden sm:flex items-center gap-0.5 text-[10px] text-muted-foreground/60">⌘K</kbd>
          </button>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => setDark((v) => !v)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Toggle theme"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            <button
              onClick={() => { setNotifOpen((v) => !v); setProfileOpen(false); }}
              className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Notifications"
            >
              <Bell size={16} />
              {unread > 0 && <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />}
            </button>

            <button
              onClick={() => { setProfileOpen((v) => !v); setNotifOpen(false); }}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg hover:bg-muted transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold font-display">A</div>
              <span className="hidden sm:block text-sm font-medium">Aviral</span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {page === "dashboard" && <Dashboard dark={dark} setPage={navigate} />}
          {page === "ai" && <AIAnalyzer />}
          {page === "quotations" && <QuotationList />}
          {page === "invoices" && <InvoiceList />}
          {page === "clients" && <ClientList />}
          {page === "projects" && <ProjectList />}
          {page === "payments" && <PaymentsPage />}
          {page === "analytics" && <AnalyticsPage dark={dark} />}
          {page === "notifications" && <NotificationsPage setPage={navigate} />}
          {page === "settings" && <SettingsPage />}
        </main>

        {/* Mobile bottom nav */}
        <nav className="md:hidden flex items-center border-t border-border bg-card px-2 py-2 safe-area-inset-bottom">
          {mobileNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              className={`flex-1 flex flex-col items-center gap-1 py-1.5 rounded-lg transition-colors relative ${page === item.id ? "text-primary" : "text-muted-foreground"}`}
            >
              <item.icon size={20} />
              {item.id === "notifications" && unread > 0 && (
                <span className="absolute top-1 right-1/2 translate-x-3 w-2 h-2 bg-primary rounded-full" />
              )}
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Mobile drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileNavOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-card border-r border-border flex flex-col animate-slide-in">
            <div className="flex items-center justify-between px-4 py-5 border-b border-border">
              <Logo />
              <button onClick={() => setMobileNavOpen(false)} className="p-1.5 rounded-lg hover:bg-muted" aria-label="Close menu"><X size={16} /></button>
            </div>
            <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
              {[...navItems, ...bottomNavItems].map((item) => (
                <button
                  key={item.id}
                  onClick={() => navigate(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${navBtnClass(item)}`}
                >
                  <item.icon size={17} />
                  <span>{item.label}</span>
                  {item.id === "notifications" && unread > 0 && (
                    <span className="ml-auto w-5 h-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center">{unread}</span>
                  )}
                </button>
              ))}
            </nav>
          </aside>
        </div>
      )}

      {/* Click-outside backdrop for dropdowns */}
      {(notifOpen || profileOpen) && (
        <div className="fixed inset-0 z-20" onClick={() => { setNotifOpen(false); setProfileOpen(false); }} />
      )}

      {/* Notification dropdown */}
      {notifOpen && (
        <div className="fixed top-14 right-4 z-30 w-80 bg-card border border-border rounded-xl shadow-lg animate-scale-in overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <p className="font-semibold text-sm">Notifications</p>
            <button onClick={() => setNotifOpen(false)} aria-label="Close"><X size={14} className="text-muted-foreground" /></button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-6 text-sm text-muted-foreground text-center">You're all caught up.</p>
            ) : (
              notifications.slice(0, 5).map((n) => (
                <div
                  key={n.id}
                  onClick={() => { markNotificationRead(n.id); if (n.relatedPage) navigate(n.relatedPage as Page); else setNotifOpen(false); }}
                  className={`flex gap-3 px-4 py-3 border-b border-border last:border-0 hover:bg-muted/40 cursor-pointer ${!n.read ? "bg-secondary/30" : ""}`}
                >
                  <div className="text-base flex-shrink-0 mt-0.5">{n.icon}</div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium leading-tight">{n.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{n.body}</p>
                    <p className="text-xs text-muted-foreground/60 mt-1">{n.time}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          <button
            onClick={() => navigate("notifications")}
            className="w-full text-center py-2.5 text-xs text-primary font-medium hover:bg-muted transition-colors"
          >
            View all notifications
          </button>
        </div>
      )}

      {/* Profile dropdown */}
      {profileOpen && (
        <div className="fixed top-14 right-4 z-30 w-56 bg-card border border-border rounded-xl shadow-lg animate-scale-in overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <p className="font-semibold text-sm">Aviral Sharma</p>
            <p className="text-xs text-muted-foreground">aviral@example.com</p>
          </div>
          {[
            { label: "Profile", icon: User },
            { label: "Business settings", icon: Building2 },
            { label: "Billing", icon: CreditCard },
            { label: "Keyboard shortcuts", icon: Zap },
          ].map((item) => (
            <button key={item.label} onClick={() => navigate("settings")} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
              <item.icon size={14} />
              {item.label}
            </button>
          ))}
          <div className="border-t border-border">
            <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-muted transition-colors" onClick={() => { setProfileOpen(false); onSignOut(); }}>
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        </div>
      )}

      {/* Command palette */}
      {cmdOpen && <CommandPalette onClose={() => setCmdOpen(false)} setPage={navigate} />}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Root                                                                */
/* ------------------------------------------------------------------ */

export default function App() {
  const [authed, setAuthed] = useState(false);

  if (!authed) return <Auth onDone={() => setAuthed(true)} />;

  return (
    <StoreProvider>
      <ModalProvider>
        <Shell onSignOut={() => setAuthed(false)} />
        <ToastHost />
      </ModalProvider>
    </StoreProvider>
  );
}