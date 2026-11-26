import { useState } from "react"
import { Head } from "@inertiajs/react"
import { FormField } from "@/Components/admin/FormField"
import { ActionDialog } from "@/Components/budgets/ActionDialog"
import { RequestList } from "@/Components/budgets/RequestList"
import { Button } from "@/Components/ui/button"
import { Textarea } from "@/Components/ui/textarea"
import { useBudgetAction } from "@/composables/useBudgetAction"
import { useRoute } from "@/composables/useRoute"
import { BudgetLayout } from "@/Layouts/BudgetLayout"

function ReviewAction({ request, decision, onClose }) {
  const route = useRoute()
  const rejecting = decision === "REJECTED"
  const label = rejecting ? "Reject request" : "Approve request"
  const { form, submit } = useBudgetAction(
    { status: decision, feedback: "", revision: request.revision },
    route("budget_review", { request_id: request.id }),
    onClose,
  )
  return (
    <ActionDialog title={label} description={`Record a final decision for “${request.title}”.`}
      onClose={onClose} onSubmit={submit} processing={form.processing}
      error={form.errors.action || form.errors.status} submitLabel={label} destructive={rejecting}>
      <FormField label={rejecting ? "Review note" : "Review note (optional)"}
        htmlFor="budget-feedback" error={form.errors.feedback} required={rejecting}>
        <Textarea id="budget-feedback" required={rejecting} maxLength={2000} rows={4}
          value={form.data.feedback} aria-invalid={!!form.errors.feedback}
          onChange={(e) => form.setData("feedback", e.target.value)} />
      </FormField>
    </ActionDialog>
  )
}

export default function Manager({ queue, history }) {
  const route = useRoute()
  const [selected, setSelected] = useState(null)
  const href = (page, past) => route("budget_manager", {}, { page, history: past })

  return (
    <>
      <Head title="Approval queue" />
      <section className="grid gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Approval queue</h1>
        <RequestList collection={queue} empty="No requests are awaiting review."
          pageHref={(page) => href(page, history.page)}
          actions={(request) => request.canReview && (
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => setSelected({ request, decision: "APPROVED" })}>Approve</Button>
              <Button size="sm" variant="outline" onClick={() => setSelected({ request, decision: "REJECTED" })}>Reject</Button>
            </div>
          )} />
      </section>
      <section className="grid gap-4">
        <h2 className="text-xl font-semibold">Request history</h2>
        <RequestList collection={history} empty="No decisions or withdrawals have been recorded."
          pageHref={(page) => href(queue.page, page)} actions={() => null} />
      </section>
      {selected && <ReviewAction {...selected} onClose={() => setSelected(null)} />}
    </>
  )
}

Manager.layout = (page) => <BudgetLayout>{page}</BudgetLayout>
