# Cluster Project

Scope
The requirements for this project are carefully selected to minimize impact on the existing applications of the hardware, and to provide accessible compute resources with minimal user setup.

Requirements

Only operate after hours
Gradual roll out (starts with 2 computers, and over the project duration roll out to all)
Alpha and beta testing
Real time monitoring and logging of the K8 environment (incl. each node)
Basic networking
Features

Kubeflow for training with PyTorch and TensorFlow
Invisible to users
A service account can host these processes in the background
Automatic wind down
During regular use, a CronJob will signal the containers to save state to PVs and scale to 0 with a 'freeze' signal. This will ensure that the entire setup has negligible impact on node resources.
Image registry
Nice to have

Access from anywhere. We could build a web interface that is hosted via Cloudflare proxy. This will also be a single point of access, and can easily implement SSO.
High throughput networking through ethernet cables and switches.
Roll out to all students.
Incident Response
We will carefully select a limited group of users to participate as testers in the alpha and beta phases of our project. These users will help us evaluate the performance, stability, and overall functionality of the system in a real-world environment.

During both the alpha and beta testing stages, we will issue a strong advisory to all participating users to ensure that they back up their data prior to using the cluster. This precaution is necessary because, at these early stages, the system is still undergoing development and rigorous testing. Consequently, there is an increased likelihood of encountering bugs, errors, or other unforeseen issues that could potentially lead to data corruption or loss.

Recognizing the critical nature of these tests, our team will commit to dedicating specific hours each week to monitor the system closely and respond promptly to any incidents that may occur. This dedicated time will be used to address any bugs, troubleshoot issues, and implement necessary fixes. Our goal is to mitigate the impact on users and ensure that any problems are resolved as quickly as possible.

Implementation Strategy
Alpha
Stage 1 [DONE]
Hardware: ISAIC VMs with GPU (Until nodes are ready)

Set up a simple cluster with minikube that can access the GPU.
Figure out how to provision resources (Jobs + CLI tool / web interface)
Set up Kubeflow
Stage 2
Hardware: 2 cluster nodes

Migrate cluster specifications to k8s
Establish service account
Connect cluster nodes
Define and configure roles
Test resource provisioning (with Kubeflow-specific workflows)
Stage 3
Hardware: 4 cluster nodes

Implement monitoring and logging
Implement wind down
Test resource provisioning
Beta
Stage 1
Hardware: 4 cluster nodes

Implement SSO
Beta user testing
Bug fixes
Stage 2
Hardware: 8 cluster nodes

Beta user testing
Bug fixes
Stage 3
Hardware: All cluster nodes

Beta user testing
Bug fixes
Questions
Why follow this implementation? Why not allow direct access via SSH?

This implementation enables several key features. First, and perhaps most importantly, it ensures that workloads are isolated, adding a crucial layer of security. Secondly, many machine learning libraries and frameworks have better support on Linux, which is effectively utilized through containerization. Additionally, this approach provides administrators with enhanced control over job scheduling, the ability to send freeze signals, and greater flexibility in managing resource allocation.

What are the components you will need to install?

WSL 2 (this might already be installed)
CUDA Drivers
NVIDIA Container Toolkit
Docker (container runtime)
Kubectl
Custom Images. These will include:
Python packages (pytorch, etc.)
CUDA, CUDArt, etc.
What is the data backup strategy?

There is no data backup strategy for now. We will advise users to store their data somewhere before sending a copy to the cluster. We will persist state in PVs, but this should not be relied on.

How much local storage do you need? How much memory do you need?

Let's start with 50GB on each node. This will be enough for the basic workloads we hope to test this semester. This can be scaled up or down based on usage down the road.

Since the computers are not going to be used during the cluster's active period, we will allocate as much memory as possible to prevent bottlenecks in the ML pipeline.

How are you setting up time sharing?

There will be a CronJob that winds up and winds down the cluster based on the time of day.

User population?

We will start with a small group of testers. This will include the people working on the cluster (Noel & Eugene), our faculty sponsor, and a select few students and ML labs.

How will you prevent the cluster from interfering with eSports applications?

The cluster is designed to wind down during the day, deallocating system resources to ensure minimal impact on other applications, including eSports. This wind-down process involves saving the current state of the cluster and scaling down resources, making the difference in system performance nearly unnoticeable to users.

Additionally, the processes associated with the cluster will be isolated using a service account that is inaccessible to non-privileged users. This ensures that the cluster operations remain separate from any eSports applications, further reducing the risk of interference.

How does the system handle multi-tenancy?

We will start by assigning namespaces to each tenant (this could be an individual or a team). This will isolate user resources and allow admins to set quotas.
