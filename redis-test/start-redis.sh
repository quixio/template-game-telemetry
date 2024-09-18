   #!/bin/sh
   # Print the container's IP address
   ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1

   # Start the Redis server
   redis-server