Vagrant.configure("2") do |config|
  # Define base box (Ubuntu 22.04)
  config.vm.box = "ubuntu/jammy64"

  # Common provisioning script for both L4S Client and Server
  $setup_l4s = <<-SCRIPT
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y linux-image-generic htop iperf3 tcptraceroute bc iproute2 net-tools dcmtk python3-pip flent netperf

    # Note: Installing the custom L4S Kernel from the PPA or downloading the .deb
    # as described in L4SkernelPatchSetUp.md. For demonstration, we simulate the module load.

    # Enable ECN
    sysctl -w net.ipv4.tcp_ecn=3
    echo "net.ipv4.tcp_ecn=3" | tee -a /etc/sysctl.conf

    # Load TCP Prague and DualPI2 (assuming L4S kernel is booted)
    modprobe tcp_prague || echo "Warning: tcp_prague module not found, requires L4S kernel reboot"
    modprobe sch_dualpi2 || echo "Warning: sch_dualpi2 module not found, requires L4S kernel reboot"

    # Set TCP Prague
    sysctl -w net.ipv4.tcp_congestion_control=prague || echo "Warning: prague not available"
    echo "net.ipv4.tcp_congestion_control=prague" | tee -a /etc/sysctl.conf

    # Apply DualPI2 AQM to the primary network interface (eth1 for private network)
    tc qdisc replace dev eth1 root dualpi2 || echo "Warning: dualpi2 not available"

    # Disable offloading (TSO, GSO, GRO)
    ethtool -K eth1 tso off gso off gro off || true

    echo "L4S setup complete on $(hostname)"
  SCRIPT

  # Define L4S Server
  config.vm.define "l4s-server" do |server|
    server.vm.hostname = "l4s-server"
    server.vm.network "private_network", ip: "192.168.50.10"

    server.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 2
      vb.name = "L4SBOA-Server"
    end

    server.vm.provision "shell", inline: $setup_l4s

    # Start the storescp server in the background
    server.vm.provision "shell", run: "always", inline: <<-SCRIPT
      mkdir -p /home/vagrant/dicom_received
      # Start storescp on port 1104
      pkill storescp || true
      su - vagrant -c "storescp -v -aet PACS_SERVER -od ~/dicom_received 1104 > ~/storescp.log 2>&1 &"

      # Start iperf3 server daemon
      pkill iperf3 || true
      su - vagrant -c "iperf3 -s -D"

      # Start netserver for flent
      pkill netserver || true
      su - vagrant -c "netserver"
    SCRIPT
  end

  # Define L4S Client
  config.vm.define "l4s-client" do |client|
    client.vm.hostname = "l4s-client"
    client.vm.network "private_network", ip: "192.168.50.20"

    client.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 2
      vb.name = "L4SBOA-Client"
    end

    client.vm.provision "shell", inline: $setup_l4s

    # Install Python testing dependencies
    client.vm.provision "shell", inline: <<-SCRIPT
      pip3 install matplotlib pandas psutil flent
    SCRIPT
  end

end