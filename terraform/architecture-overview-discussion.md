## Architecture Overview (Discussion)

This infrastructure design balances cost, reliability, and operational simplicity by leveraging serverless components to orchestrate a short-lived compute resource. Rather than running a continuously active EC2 instance, the system spins up compute only when policies must be enforced, minimizing idle charges and reducing operational overhead.

### Context & Rationale  
- **Cost Control**  
  Traditional always-on EC2 deployments incur baseline costs even when idle. By scheduling an EventBridge rule to awaken the EC2 instance just for policy execution, we shift to a usage-based model. This approach is especially valuable for environments where custodial scans run on predictable intervals (e.g., nightly or hourly).  

- **Operational Simplicity**  
  Using a small Lambda function to start the instance avoids managing a fleet of scheduled hosts. There’s no need for complex autoscaling groups or cron jobs on the instance itself. When the scan completes, the instance shuts itself down, returning the environment to a zero-running-resource state.

### Design Decisions  
1. **EventBridge vs. Native Cron on EC2**  
   - *Why EventBridge?* Centralized scheduling, built-in retries, and native AWS integration.  
   - *Alternate:* A cron daemon inside a continuously running instance—but that defeats the cost-saving goal.  

2. **Lambda for Orchestration**  
   - A lightweight function is faster and cheaper to maintain than a dedicated orchestration service.  
   - *Alternate:* Step Functions could model more complex workflows (e.g., conditional logic before start), but adds cost and configuration overhead.

3. **EC2 with Docker**  
   - Running Cloud Custodian in Docker ensures environment consistency and easy version management.  
   - *Alternate:* Fargate or ECS on scheduled tasks offers a fully serverless compute option but can introduce cold-start latency and higher per-GB pricing, making EC2 preferable at moderate scale.

### Alternatives & Trade-Offs  
- **Fargate Scheduled Tasks**  
  - *Pros:* No EC2 to manage, pay per second.  
  - *Cons:* Potential cold-start delays, per-vCPU memory pricing may exceed occasional EC2 spot or burstable instances.  

- **ECS Cluster with Spot Instances**  
  - *Pros:* Shares capacity across tasks, spot pricing reduces cost.  
  - *Cons:* Requires cluster management, spot interruptions can disrupt scheduled scans.

- **Always-On Small Instance**  
  - *Pros:* Simplest execution model.  
  - *Cons:* Incurs baseline cost 24/7; may run idle >95% of time.

### Broader Perspective  
This pattern exemplifies a “serverless control plane” managing a transient “container data plane.” It extends beyond Cloud Custodian: any batch or periodic workload that needs an environment with specific dependencies can adopt the same skeleton. By decoupling scheduling, orchestration, and execution, teams gain flexibility to swap in alternative compute (e.g., containers on Kubernetes, Step Functions, or even on-prem runners) without rewriting the core startup/shutdown logic.