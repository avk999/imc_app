# Sender selector
 webapp to choose the best data sender
## Parameters analyzed:
* Lost packets
* Malformed packets
* Delay (as sum of delays compared to the first packet)
* Jitter (max and avg)
* consensus on Symbol and Price (not analyzed automatically, just shown)
* Those parameters are (arbitrary) scored and two best senders are selected.
## Input:
The tool requires a PCAP file. PCAP file should contain only the relevant packets, be continuous in time. It is assumed that senders send data with constant frequency (otherwise jitter analysis doesn't make sense)
## Output:
resulting HTML is saved in the subdirectory of output directory
## Environment variables:
    * UPLOADS - where to store PCAP files, by default /tmp
    * OUTPUTS - directory for reports, no default
## Requiremens: python3, moduels in requirements.txt 
## TODO: 
* error handling
* consensus analysis
* think more about jitter