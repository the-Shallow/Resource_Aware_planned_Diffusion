#include "scheduler.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <unordered_set>

namespace semantic_parallel::scheduler {
    std::vector<WorkerAssignment> schedule_round_robin(
        const std::vector<TaskSpec>& tasks,
        std::int64_t worker_count
    ) {
        if(worker_count <= 0){
            throw std::invalid_argument("worker count must be greater than zero.");
        }

        std::unordered_set<std::int64_t> seen_chunk_ids;

        for(const TaskSpec& task : tasks){
            if(task.chunk_id < 0){
                throw std::invalid_argument("chunk id must be nonnegative");
            }

            if(!std::isfinite(task.estimated_cost) || 
                task.estimated_cost < 0.0){
                    throw std::invalid_argument("estimated cost must be finite and nonnegative");
                }
            
            if(!seen_chunk_ids.insert(task.chunk_id).second){
                throw std::invalid_argument("chunk id values must be unique");
            }
        }

        std::vector<TaskSpec> ordered_tasks = tasks;

        std::sort(ordered_tasks.begin(), ordered_tasks.end(), 
            [](const TaskSpec& left, const TaskSpec& right){
                return left.chunk_id < right.chunk_id;
            });

        std::vector<WorkerAssignment> assignments;
        assignments.reserve(static_cast<std::size_t>(worker_count));

        for(std::int64_t worker_id = 0; worker_id < worker_count; ++worker_id){
            assignments.push_back({worker_id, {}, 0.0});
        }

        for(std::size_t task_idx = 0; task_idx < ordered_tasks.size(); ++task_idx){
            const std::size_t worker_idx = task_idx % assignments.size();

            const TaskSpec& task = ordered_tasks[task_idx];

            assignments[worker_idx].chunk_ids.push_back(task.chunk_id);
            assignments[worker_idx].estimated_load += task.estimated_cost;
        }

        return assignments;
    }
}