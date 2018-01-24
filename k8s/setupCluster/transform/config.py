# from pathlib import Path
import os
from string import Template

TestDir = './dest/'
PORTSTARTFROM = 30500
GAP = 100  # interval for worker's port


def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))

        ##### For testing ########################
        ##testDest = dest.split("/")[-1]	##
        ##with open(TestDir+testDest, 'w') as d:##
        ##d.write(t.substitute(**kw))      	##
        ##########################################


def condRender(src, dest, override, **kw):
    if not os.path.exists(dest):
        render(src, dest, **kw)
    elif os.path.exists(dest) and override:
        render(src, dest, **kw)


def getTemplate(templateName):
    baseDir = os.path.dirname(__file__)
    configTemplate = os.path.join(baseDir, "../templates/" + templateName)
    return configTemplate


def configKafkaNamespace(path, override):
    namespaceTemplate = getTemplate("template_pod_kafka_namespace.yaml")
    condRender(namespaceTemplate, path + "/" + "kafka-namespace.yaml", override)


def configZookeepers(path, override, all_volumes):
    for i in range(0, 3):
        zkTemplate = getTemplate("template_pod_zookeeper.yaml")
        zkPodName = "zookeeper" + str(i) + "-kafka"
        zookeeperID = "zookeeper" + str(i)
        seq = i + 1
        nodePort1 = 32750 + (i * 3 + 1)
        nodePort2 = 32750 + (i * 3 + 2)
        nodePort3 = 32750 + (i * 3 + 3)
        zooServersTemplate = "server.1=zookeeper0.kafka:2888:3888 server.2=zookeeper1.kafka:2888:3888 server.3=zookeeper2.kafka:2888:3888"
        zooServers = zooServersTemplate.replace("zookeeper" + str(i) + ".kafka", "0.0.0.0")

        zk_log_volume = ""
        if len(all_volumes['zk_log']) > i:
            zk_log_volume = all_volumes['zk_log'][i]
        zk_data_volume = ""
        if len(all_volumes['zk_data']) > i:
            zk_data_volume = all_volumes['zk_data'][i]
        condRender(zkTemplate, path + "/" + zookeeperID + "-zookeeper.yaml", override,
                   zkPodName=zkPodName, zookeeperID=zookeeperID, seq=seq, zooServers=zooServers,
                   nodePort1=nodePort1, nodePort2=nodePort2, nodePort3=nodePort3,
                   logVolume=zk_log_volume, dataVolume=zk_data_volume)


def configKafkas(path, override, all_volumes):
    for i in range(0, 4):
        kafkaTemplate = getTemplate("template_pod_kafka.yaml")
        kafkaPodName = "kafka" + str(i) + "-kafka"
        kafkaID = "kafka" + str(i)
        seq = i
        nodePort1 = 32730 + (i * 2 + 1)
        nodePort2 = 32730 + (i * 2 + 2)
        advertisedHostname = "kafka" + str(i) + ".kafka"

        kafka_volume = ""
        if len(all_volumes['kafka']) > i:
            kafka_volume = all_volumes['kafka'][i]
        condRender(kafkaTemplate, path + "/" + kafkaID + "-kafka.yaml", override,
                   kafkaPodName=kafkaPodName, kafkaID=kafkaID, seq=seq,
                   advertisedHostname=advertisedHostname, nodePort1=nodePort1,
                   nodePort2=nodePort2, volumeId=kafka_volume)


# create org/namespace
def configORGS(name, path, orderer0,
               override, index,
               all_volumes, nfs,
               ex_ports):  # name means if of org, path describe where is the namespace yaml to be created.
    namespaceTemplate = getTemplate("template_pod_namespace.yaml")
    namespace = name.replace(".", "-")
    condRender(namespaceTemplate, path + "/" + name + "-namespace.yaml", override,
               org=namespace,
               pvName=name + "-pv",
               path=path.replace("transform/../", "/"),
               nfs=nfs
               )

    if path.find("peer") != -1:
        ####### pod config yaml for org cli
        cliTemplate = getTemplate("template_pod_cli.yaml")

        mspPathTemplate = 'users/Admin@{}/msp'
        orderer0pv = orderer0 + "-" + name + "-pv"
        tlsPathTemplate = 'users/Admin@{}/tls'

        condRender(cliTemplate, path + "/" + name + "-cli.yaml", override, name="cli",
                   namespace=namespace,
                   mspPath=mspPathTemplate.format(name),
                   tlsPath=tlsPathTemplate.format(name),
                   pvName=name + "-pv",
                   artifactsName=name + "-artifacts-pv",
                   peerAddress="peer0." + name + ":7051",
                   mspid=name.split('-')[0].capitalize() + "MSP",
                   orderer0pv=orderer0pv, orderer0=orderer0, nfs=nfs)
        #######

        ####### pod config yaml for org ca

        ###Need to expose pod's port to worker ! ####
        ##org format like this org1-f-1##
        addressSegment = index * GAP
        exposedPort = PORTSTARTFROM + addressSegment + 95

        caTemplate = getTemplate("template_pod_ca.yaml")

        tlsCertTemplate = '/etc/hyperledger/fabric-ca-server-config/ca/{}-cert.pem'
        tlsKeyTemplate = '/etc/hyperledger/fabric-ca-server-config/ca/{}'
        caPathTemplate = 'ca/'
        # tlsPathTemplate = 'tlsca/'
        cmdTemplate = ' fabric-ca-server start --ca.certfile /etc/hyperledger/fabric-ca-server-config/ca/{}-cert.pem --ca.keyfile /etc/hyperledger/fabric-ca-server-config/ca/{} -b admin:adminpw -d '

        skFile = ""
        for f in sorted(os.listdir(path + "/ca")):  # find out sk!
            if f.endswith("_sk"):
                skFile = f

        # tlsSKFile = ""
        # for f in os.listdir(path + "/tlsca"):  # find out sk!
        #     if f.endswith("_sk"):
        #         tlsSKFile = f
        ca_volume = ""
        if len(all_volumes['ca']) > index and len(all_volumes['ca'][index]) > 0:
            ca_volume = all_volumes['ca'][index][0]
        if len(ex_ports['ca']) > index:
            if ex_ports['ca'][index] != "":
                org_ex_port = ex_ports['ca'][index]
                exposedPort = int(org_ex_port) + 95
        condRender(caTemplate, path + "/" + name + "-ca.yaml", override,
                   namespace=namespace,
                   command='"' + cmdTemplate.format("ca." + name, skFile) + '"',
                   caPath=caPathTemplate,
                   tlsKey=tlsKeyTemplate.format(skFile),
                   tlsCert=tlsCertTemplate.format("ca." + name),
                   nodePort=exposedPort,
                   pvName=name + "-pv",
                   volumeId=ca_volume
                   )
        #######


def generateYaml(member, memberPath, flag, override, orgindex, nodeindex, all_volumes, ex_ports):
    if flag == "/peers":
        configPEERS(member, memberPath, override, orgindex, nodeindex, all_volumes, ex_ports)
    else:
        configORDERERS(member, memberPath, override, orgindex, nodeindex, all_volumes, ex_ports)


        # create peer/pod


def configPEERS(name, path, override, orgindex, peerindex, all_volumes, ex_ports):  # name means peerid.
    configTemplate = getTemplate("template_pod_peer.yaml")

    mspPathTemplate = 'peers/{}/msp'
    tlsPathTemplate = 'peers/{}/tls'
    # mspPathTemplate = './msp'
    # tlsPathTemplate = './tls'
    peerName = name[0:name.index(".")]
    orgName = name[name.index(".") + 1:]

    addressSegment = orgindex * GAP
    ##peer from like this peer 0##
    peerOffset = peerindex * 3
    exposedPort1 = PORTSTARTFROM + addressSegment + peerOffset
    exposedPort2 = PORTSTARTFROM + addressSegment + peerOffset + 1
    exposedPort3 = PORTSTARTFROM + addressSegment + peerOffset + 2

    namespace = orgName.replace(".", "-")
    serviceName = peerName + "." + namespace
    peer_volume = ""

    print(len(all_volumes['peer']))
    print(len(all_volumes['peer'][orgindex]))
    if len(all_volumes['peer']) > orgindex and len(all_volumes['peer'][orgindex]) > peerindex:
        print(orgindex)
        print(peerindex)
        peer_volume = all_volumes['peer'][orgindex][peerindex]
        print(peer_volume)
    if len(ex_ports['peer']) > orgindex:
        if ex_ports['peer'][orgindex] != "":
            org_ex_port = ex_ports['peer'][orgindex]
            exposedPort1 = int(org_ex_port) + peerOffset
            exposedPort2 = int(org_ex_port) + peerOffset + 1
            exposedPort3 = int(org_ex_port) + peerOffset + 2
    condRender(configTemplate, path + "/" + name + ".yaml", override,
               namespace=namespace,
               podName=peerName + "-" + namespace,
               peerID=peerName,
               # org=orgName,
               corePeerID=serviceName,
               peerAddress=serviceName + ":7051",
               peerGossip=serviceName + ":7051",
               localMSPID=orgName.split('-')[0].capitalize() + "MSP",
               mspPath=mspPathTemplate.format(name),
               tlsPath=tlsPathTemplate.format(name),
               nodePort1=exposedPort1,
               nodePort2=exposedPort2,
               nodePort3=exposedPort3,
               pvName=orgName + "-pv",
               volumeId=peer_volume
               )


# create orderer/pod
def configORDERERS(name, path, override, orgindex, ordererindex, all_volumes, ex_ports):  # name means ordererid
    configTemplate = getTemplate("template_pod_orderer.yaml")

    mspPathTemplate = 'orderers/{}/msp'
    tlsPathTemplate = 'orderers/{}/tls'

    ordererName = name[0:name.index(".")]
    orgName = name[name.index(".") + 1:]

    addressSegment = orgindex * GAP
    ##peer from like this peer 0##
    ordererOffset = ordererindex
    exposedPort = 32000 + addressSegment + ordererOffset

    namespace = orgName.replace(".", "-")
    orderer_volume = ""
    if len(all_volumes['orderer']) > orgindex and len(all_volumes['orderer'][orgindex]) > ordererindex:
        orderer_volume = all_volumes['orderer'][orgindex][ordererindex]
    if len(ex_ports['orderer']) > orgindex:
        if ex_ports['orderer'][orgindex] != "":
            org_ex_port = ex_ports['orderer'][orgindex]
            exposedPort = int(org_ex_port) + ordererOffset
    condRender(configTemplate, path + "/" + name + ".yaml", override,
               namespace=namespace,
               ordererID=ordererName,
               podName=ordererName + "-" + namespace,
               localMSPID=orgName.split("-")[0].capitalize() + "MSP",
               mspPath=mspPathTemplate.format(name),
               tlsPath=tlsPathTemplate.format(name),
               nodePort=exposedPort,
               pvName=orgName + "-pv",
               volumeId=orderer_volume
               )

