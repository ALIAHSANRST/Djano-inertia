import { useForm } from "@inertiajs/react"

export function useBudgetAction(initial, url, onClose) {
  const form = useForm(initial)
  const submit = (event) => {
    event.preventDefault()
    form.post(url, { preserveScroll: true, onSuccess: onClose })
  }
  return { form, submit }
}
