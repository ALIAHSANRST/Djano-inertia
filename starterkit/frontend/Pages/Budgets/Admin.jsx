import { useState } from "react"
import { Head } from "@inertiajs/react"
import { ActionDialog } from "@/Components/budgets/ActionDialog"
import { RequestList } from "@/Components/budgets/RequestList"
import { Button } from "@/Components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/Components/ui/card"
import { useBudgetAction } from "@/composables/useBudgetAction"
import { useRoute } from "@/composables/useRoute"
import { AdminLayout } from "@/Layouts/AdminLayout"

function DeleteAction({ request, onClose }) {
  const route = useRoute()
  const { form, submit } = useBudgetAction({}, route("budget_delete", { request_id: request.id }), onClose)
  return <ActionDialog title="Permanently delete request"
    description={`Delete “${request.title}” and its review history. This cannot be undone.`}
    onClose={onClose} onSubmit={submit} processing={form.processing}
    error={form.errors.action} submitLabel="Delete permanently" destructive />
}

export default function Admin({ requests, totals }) {
  const route = useRoute()
  const [selected, setSelected] = useState(null)

  return (
    <>
      <Head title="Budget administration" />
      <h1 className="text-2xl font-semibold tracking-tight">Budget administration</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        {[[ "Pending funding", totals.pending ], [ "Approved funding", totals.approved ]].map(([label, amount]) => (
          <Card key={label}>
            <CardHeader><CardTitle className="text-base">{label}</CardTitle></CardHeader>
            <CardContent className="text-2xl font-semibold tabular-nums">{amount}</CardContent>
          </Card>
        ))}
      </div>
      <section className="grid gap-4">
        <h2 className="text-xl font-semibold">All requests</h2>
        <RequestList collection={requests} empty="No budget requests have been submitted."
          pageHref={(page) => route("budget_admin", {}, { page })}
          actions={(request) => request.canDelete && (
            <div><Button size="sm" variant="destructive" onClick={() => setSelected(request)}>Delete</Button></div>
          )} />
      </section>
      {selected && <DeleteAction request={selected} onClose={() => setSelected(null)} />}
    </>
  )
}

Admin.layout = (page) => <AdminLayout budget>{page}</AdminLayout>
