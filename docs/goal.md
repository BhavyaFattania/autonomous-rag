## Possible asked questions

### Architecture questions

1. why did you choose langgraph instead of a simple while loop?
Answer: because the workflow is not only the try --> evaluate --> repeat 
it contains multiple stages such as reflection, deplicate detection etc. langgraph makes that explicit and resumable using the checkpointer. so it is more suitable for overnight runs.

2. why separate scientist and reflection?

