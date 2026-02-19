-- Allow users to delete their own job queue entries (dismiss jobs from dashboard)
CREATE POLICY user_job_queue_delete ON user_job_queue
    FOR DELETE USING (auth.uid() = user_id);
