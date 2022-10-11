# IMC Trading Infrastructure - Linux Engineer assignment

Thank you in advance for taking the time and effort to complete the assignment below. Once you complete the challenge, please leave the deployment running so we can verify the results. 

The purpose of this test is not only to evaluate your technical skills but also your ability to interpret requirements. At IMC, we value clean and maintainable code so we will also look at readability and correctness of your contribution.

The market data from the aforementioned sources is identical (for redundancy and scalability reasons) and the only difference is the arrival time at our datacenter(s). 

We are very interested in the fastest arrival times since it allows our trading machines to react faster on opportunities in the markets. 

In this particular case, we are receiving identical data sets from four different multicast publishers on separate lines. Each packet contains data in plain ASCII. 

For example: 
```
Symbol: APPL Seqno: 977 Price: 1696
Symbol – represents the traded product, in this case Apple. 
Seqno – unique sequence number per event and packet
Price – the new price for this product. 
```
The Exchange normally charges their customers for each line and we would like to keep only two out of the four lines. 

Your assignment is split in two parts. 

### 1. Programming section

First, we would like you to use a programming language of your choice in order to process and analyze data for this assignment. The data is provided a .pcap file that you can find in the home directory of this host. Your code should provide summary metrics for each network line (source IP) that demonstrate how they compare in terms of arrival times and clearly show which two network lines are the ones that should be kept. Your code should provide text output or graphical visualization (or both) for presentation to your colleagues. 

Please also explain your reasoning behind the choice: Why are you choosing to keep the two lines (less jitter, fewer drops, etc)?

### 2. Deployment section

Second, we would like you to deploy your code inside a standalone kubernetes cluster that should run on this host.
It is at your discretion how you deploy your cluster and your workload on it. The deployment should persist the results on disk.

We expect to be able to log into the host and verify your work. This will consist in:
Leaving the host, containers, pods, deployment, etc. running, so we can view how the solution was implemented.
Keeping all files used (.yaml, .py, Dockerfile, readme, etc.) available on the host.
Viewing the analysis output from your application using the appropriate method that you specify (vi a txtfile, open an .html file with a browser, etc.). 

Please provide any more detailed instructions you think we will need to run your application.

You have 48 hours to complete the assignment, but we expect the task to not take much longer than 4 hours. 

We hope that you enjoy solving this challenge and wish you good luck!
