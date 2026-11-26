import { useState } from "react"
import { Head } from "@inertiajs/react"
import { FormField } from "@/Components/admin/FormField"
import { ActionDialog } from "@/Components/budgets/ActionDialog"
import { RequestList } from "@/Components/budgets/RequestList"
import { Button } from "@/Components/ui/button"
import { Input } from "@/Components/ui/input"
import { Textarea } from "@/Components/ui/textarea"
import { useBudgetAction } from "@/composables/useBudgetAction"
import { useRoute } from "@/composables/useRoute"
import { BudgetLayout } from "@/Layouts/BudgetLayout"

function ClientAction({ action, request, onClose }) {
  const route = useRoute()
  const isWithdrawal = action === "withdraw"
  const labels = { create: "Submit request", update: "Save changes", withdraw: "Withdraw request" }
  const { form, submit } = useBudgetAction(
    isWithdrawal ? { revision: request.revision } : {
      revision: request?.revision ?? null,
      title: request?.title ?? "",
      amount: request?.amount ?? "",
      justification: request?.justification ?? "",
    },
    route(`budget_${action}`, request ? { request_id: request.id } : {}),
    onClose,
  )

  return (
    <ActionDialog
      title={action === "update" ? "Edit budget request" : labels[action]}
      description={isWithdrawal ? `Withdraw “${request.title}” from the approval queue.` : "Enter the requested amount and business justification."}
      onClose={onClose} onSubmit={submit} processing={form.processing}
      error={form.errors.action} submitLabel={labels[action]} destructive={isWithdrawal}
    >
      {!isWithdrawal && (
        <>
          <FormField label="Title" htmlFor="budget-title" error={form.errors.title} required>
            <Input id="budget-title" required maxLength={160} value={form.data.title}
              aria-invalid={!!form.errors.title} onChange={(e) => form.setData("title", e.target.value)} />
          </FormField>
          <FormField label="Amount" htmlFor="budget-amount" error={form.errors.amount} required>
            <Input id="budget-amount" type="number" min="0.01" step="0.01" required value={form.data.amount}
              aria-invalid={!!form.errors.amount} onChange={(e) => form.setData("amount", e.target.value)} />
          </FormField>
          <FormField label="Business justification" htmlFor="budget-justification" error={form.errors.justification} required>
            <Textarea id="budget-justification" required maxLength={4000} rows={4} value={form.data.justification}
              aria-invalid={!!form.errors.justification} onChange={(e) => form.setData("justification", e.target.value)} />
          </FormField>
        </>
      )}
    </ActionDialog>
  )
}

export default function Client({ requests }) {
  const route = useRoute()
  const [selected, setSelected] = useState(null)

  return (
    <>
      <Head title="My Requests" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">My Requests</h1>
        <Button onClick={() => setSelected({ action: "create" })}>New request</Button>
      </div>
      <RequestList collection={requests} empty="You have no budget requests."
        pageHref={(page) => route("budget_client", {}, { page })}
        actions={(request) => request.canEdit && (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => setSelected({ action: "update", request })}>Edit</Button>
            <Button size="sm" variant="outline" onClick={() => setSelected({ action: "withdraw", request })}>Withdraw</Button>
          </div>
        )} />
      {selected && <ClientAction {...selected} onClose={() => setSelected(null)} />}
    </>
  )
}

Client.layout = (page) => <BudgetLayout>{page}</BudgetLayout>
