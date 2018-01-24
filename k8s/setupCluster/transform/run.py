import os
from time import sleep

BASEDIR = os.path.dirname(__file__)
ORDERER = os.path.join(BASEDIR,
                       "../crypto-config/ordererOrganizations")  # it must point to the ordererOrgnaizations dir
PEER = os.path.join(BASEDIR, "../crypto-config/peerOrganizations")  # it must point to the peerOrgnaizations dir
KAFKA = os.path.join(BASEDIR, "../crypto-config/kafka")

### order of run ###

#### orderer
##### namespace(org)
###### single orderer

#### peer
##### namespace(org)
###### ca
####### single peer

def runOrderers(path):
    orgs = sorted(os.listdir(path))
    for org in orgs:
        orgPath = os.path.join(path, org)
        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml")  # orgYaml namespace.yaml
        checkAndRun(namespaceYaml)

        for orderer in sorted(os.listdir(orgPath + "/orderers")):
            ordererPath = os.path.join(orgPath + "/orderers", orderer)
            ordererYaml = os.path.join(ordererPath, orderer + ".yaml")
            checkAndRun(ordererYaml)
            # sleep(5)


def runPeers(path):
    orgs = sorted(os.listdir(path))
    for org in orgs:
        orgPath = os.path.join(path, org)

        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml")  # namespace.yaml
        checkAndRun(namespaceYaml)

        caYaml = os.path.join(orgPath, org + "-ca.yaml")  # namespace.yaml
        checkAndRun(caYaml)

        cliYaml = os.path.join(orgPath, org + "-cli.yaml")  # namespace.yaml
        checkAndRun(cliYaml)

        for peer in sorted(os.listdir(orgPath + "/peers")):
            peerPath = os.path.join(orgPath + "/peers", peer)
            peerYaml = os.path.join(peerPath, peer + ".yaml")
            checkAndRun(peerYaml)


def runKafkas(path):
    namespaceYaml = os.path.join(path, "kafka-namespace.yaml")
    checkAndRun(namespaceYaml)

    for i in range(0, 3):
        zkYaml = os.path.join(path, "zookeeper" + str(i) + "-zookeeper.yaml")
        checkAndRun(zkYaml)
        # sleep(3)

    for i in range(0, 4):
        kafkaYaml = os.path.join(path, "kafka" + str(i) + "-kafka.yaml")
        checkAndRun(kafkaYaml)
        # sleep(5)


def checkAndRun(f):
    if os.path.isfile(f):
        os.system("kubectl create -f " + f+" --save-config")

    else:
        print("file %s no exited" % (f))


if __name__ == "__main__":
    runKafkas(KAFKA)
    # sleep(60)
    runOrderers(ORDERER)
    runPeers(PEER)
