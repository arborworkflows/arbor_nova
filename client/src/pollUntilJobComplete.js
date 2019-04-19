export default async (girderRest, job, updateJob) => {
  // INACTIVE = 0
  // QUEUED = 1
  // RUNNING = 2
  // SUCCESS = 3
  // ERROR = 4
  // CANCELED = 5
  const delay = t => new Promise(resolve => {
    setTimeout(resolve, t);
  });
  const finalStates = [3, 4, 5];
  while (finalStates.indexOf(job.status) === -1) {
    await delay(500);
    job = (await girderRest.get(`job/${job._id}`)).data;
    updateJob(job);
  }
  return job;
}
