import { Suspense } from "react"
import { PipelineRun } from "@/components/pipeline-run"

export default function PipelinePage() {
  return (
    <Suspense>
      <PipelineRun />
    </Suspense>
  )
}
