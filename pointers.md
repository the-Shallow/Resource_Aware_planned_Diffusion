So I’d call checkpoint 1 implemented for non-cached generation, with model-output equivalence still unverified.


Scheduler implmentation checkpoints: -- 

Distribute chunks among gpus



Things to look out for: -- 
9. There is one technical wrinkle: positional encoding
This is something I didn't want to gloss over.
Suppose the original combined sequence is:
positions

0 ... 99     context + plan

100 ... 131  Chunk A
132 ... 183  Chunk B
184 ... 205  Chunk C

GPU 2 receives only:
context + plan + Chunk C

If we naïvely remove A and B, then Chunk C might become positions:
100 ... 121

instead of:
184 ... 205.

Dream uses rotary positional embeddings, so that difference can affect results.
Fortunately the model already accepts position_ids. GitHub
So we'd need our generation runtime to tell GPU 2:
These tokens physically sit next to the prefix in your local tensor,

BUT logically their positions are 184...205.

In other words:
GPU2 local storage:

prefix      Chunk C
0...99      100...121

logical position IDs:

0...99      184...205

This is a generation-runtime modification, not a Dream-7B architecture rewrite.
But it's something we'd have to get right.


10. KV caching also helps us
Their cached implementation already does quite a bit of engineering.
It caches the previously generated context and detects when chunks have completed. Completed blocks can stop being recomputed. GitHub
For us, each GPU could do:
                    GPU 0
                      │
       prefill prompt + plan once
                      │
                cache K/V
                      │
            repeatedly denoise A

Same for GPU 1 etc.
The common prefix is duplicated across GPUs, but it only needs to be prefetched once.
We don't need to communicate the huge KV cache.
Every GPU can independently compute its own copy.
That trades:
\[
\text{extra replicated memory}
\]
for:
\[
\text{almost no communication}.
\]
For latency optimization on 2–4 GPUs, that's a very reasonable trade.


12. We can make the scheduler smarter than just token count
At first:
\[
C_k=l_k
\]
where \(l_k\) is chunk length.

But perhaps actual GPU cost behaves more like:
\[
C_k=f(l_k,\text{prefix length})
\]
because attention and denoising have nonlinear costs.
So Phase 1:
cost(chunk) = predicted length

Phase 2:
profile Dream and build something like:
\[
\hat C_k=a l_k+b l_k^2.
\]
Then schedule using predicted execution cost rather than simply token length.

Random / round-robin scheduling

       ↓

Length-aware scheduling

        ↓

Profile-based cost-aware scheduling


14. And that actually gives us a very strong research question
Instead of promising:
“We'll make Planned Diffusion 4× faster.”

our project asks:
When should semantic parallelism be mapped across GPUs rather than executed as intra-GPU parallelism?

That's much better scientifically.
We could discover a crossover.
For example, completely hypothetical:
Avg chunk size	1 GPU combined	2 GPU	4 GPU
10 tokens	20 ms	22	28
30	40	30	32
60	80	48	35
120	160	90	52


Then the runtime could decide:
small chunks
→ keep them together on one GPU

medium chunks
→ use 2 GPUs

large / many chunks
→ use 4 GPUs

Now we're doing adaptive semantic parallelism.
That is considerably stronger than blindly distributing everything.


Yes. Implement static allocation first, then add dynamic dispatch within the same checkpoint.
Recommended order:
1. Static round robin
   - Assign every chunk before execution.
   - Establish the C++ interface, deterministic assignments, validation, and worker-load reporting.
2. Static LPT
   - Sort chunks by predicted length, largest first.
   - Assign each to the currently least-loaded worker.
   - Verify the 120/80/35/20 example and edge cases.
3. Static mock runtime
   - Execute each worker’s assigned list.
   - Validate barriers, result reconstruction by chunk_id, timing, and idle-time metrics.
4. Dynamic shared queue
   - Keep unstarted chunks in a central queue.
   - Whenever a worker becomes idle, it requests the next chunk.
   - Test FIFO/round-robin order first, followed by longest-first priority.
   - A chunk already executing remains on its worker; there is no preemption.
5. Compare static and dynamic
   - Test 1, 2, and 4 workers with uneven chunk costs.
   - Record makespan, worker idle time, estimated load, and completion order.
   - Confirm reconstructed output remains in original chunk_id order.
The static version gives us a simple correctness reference. Dynamic dispatch then changes only how workers obtain tasks, while task representation, execution, gathering, and reconstruction remain the same.
Profile-based cost estimation should remain later because it needs real measurements. The dynamic queue can initially prioritize chunks using content_length.