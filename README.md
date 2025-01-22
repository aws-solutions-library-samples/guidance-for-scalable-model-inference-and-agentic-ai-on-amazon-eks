# EKS-LLM



## Getting started

The main goal for this repo is to make it easier for the audience to test and validate multiple LLMs with different runtime engines on EKS.
This repo aims to provide the following. 
1. A simple script to deploy EKS with Karpenter NodePools for CPU, Kuberay and OSS observability stack. This script is available at base_eks_setup folder. Make sure you have authenticated with aws cli before running this. The script will provision a cluster in the Sydney region, install Grafna/Prometheus and KubeRay to serve models.
2. Ray Servers to serve LLama.cpp (CPU) and VLLM models (GPU). The ray-server folder contains the python code that enables RayServe to serve the model usin gLLaMa.cpp engine.
3. Ray Services to deploy clusters on EKS. Ray cluster configuration is available at ray-services folder. 
4. Once you deploy your Ray clutser, you can provision load balancer via ra-services/ingress folder.
5. Performace scripts to capture and select what works for you. The docketfiles/benchmark folder a GO program to hit the deploymed model over HTTP

>> *Warning
>> Make sure to change the HF ID in the ray-services/ray-service-vllm-llama-3.2-CPU-LLAMA.yaml and ray-service-vllm-llama-3.2-CPU-LLAMA-arm.yaml files

Please refer to the blog XXX that utilises thses scripts for a measurements of Intel vs Graviton.

## Contact
Please contact wangaws@ or fmamazon@ if you want to know more and/or contribute.