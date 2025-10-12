import type { TelemetryRegister } from '@/types'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { TELEMETRY_QUERY_KEY, useUpdateTelemetryMutation } from '@/hooks/module'

interface Props {
  open: boolean
  setOpen: (open: boolean) => void
  register: TelemetryRegister
  moduleAddress: number
}
export default function EditValueRegisterDialog({ open, setOpen, register, moduleAddress }: Props) {
  const queryClient = useQueryClient()
  const { mutate: updateTelemetry, isPending } = useUpdateTelemetryMutation()

  const FormSchema = z.object({
    value: z.number(),
  })
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      value: undefined,
    },
  })

  const handleUpdateTelemetry = (data: z.infer<typeof FormSchema>) => {
    updateTelemetry({
      address: moduleAddress,
      value: Number(data.value),
      register_address: register.address,
      force: false,
    }, {
      onSuccess: () => {
        toast.success('Telemetry updated successfully')
        queryClient.invalidateQueries({ queryKey: [TELEMETRY_QUERY_KEY, moduleAddress] })
      },
      onError: () => {
        toast.error('Failed to update telemetry')
      },
    })
    setOpen(false)
  }

  useEffect(() => {
    if (open) {
      form.reset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleUpdateTelemetry)} className="space-y-4">
            <DialogHeader>
              <DialogTitle>
                Edit
                <span className="text-primary">
                  {` ${register.name} `}
                </span>
                Register
                <span className="font-mono text-sm text-muted-foreground">
                  {` (${register.address})`}
                </span>
              </DialogTitle>
              <DialogDescription className="sr-only"></DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-[5fr_1fr_5fr] gap-2 px-2 text-base">
              {/* Current value */}
              <Label>Current Value</Label>
              <span className="col-start-1 row-start-2">{register.value}</span>

              <ChevronRight className="col-start-2 row-start-2 self-center size-4" />

              {/* New value */}
              <Label className="col-start-3 row-start-1">New Value</Label>
              <FormField
                control={form.control}
                name="value"
                render={({ field }) => (
                  <>
                    <FormItem className="col-start-3 row-start-2">
                      <FormControl>
                        <Input
                          className="!text-base"
                          type="number"
                          inputMode="numeric"
                          {...field}
                          onChange={e => field.onChange(e.target.value && (field.value = Number(e.target.value)))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  </>
                )}
              />
            </div>
            <DialogFooter>
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
