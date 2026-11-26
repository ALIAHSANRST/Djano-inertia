import { Head, Link } from "@inertiajs/react"
import { Button } from "@/Components/ui/button"
import { useRoute } from "@/composables/useRoute"
import { BudgetLayout } from "@/Layouts/BudgetLayout"

export default function ErrorPage({ status, message }) {
  const route = useRoute()
  const title = status === 403 ? "Access denied" : "Request unavailable"
  return (
    <div className="grid justify-items-start gap-4">
      <Head title={title} />
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p role="alert" className="text-muted-foreground">{message}</p>
      <Button asChild><Link href={route("budget_index")}>Back to your dashboard</Link></Button>
    </div>
  )
}

ErrorPage.layout = (page) => <BudgetLayout>{page}</BudgetLayout>
