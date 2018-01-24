import os

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

def deleteOrderers(path):
    orgs = sorted(os.listdir(path))
    for org in orgs:
        orgPath = os.path.join(path, org)
        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml")  # orgYaml namespace.yaml

        for orderer in sorted(os.listdir(orgPath + "/orderers")):
            ordererPath = os.path.join(orgPath + "/orderers", orderer)
            ordererYaml = os.path.join(ordererPath, orderer + ".yaml")
            checkAndDelete(ordererYaml)

        checkAndDelete(namespaceYaml)


def deletePeers(path):
    orgs = sorted(os.listdir(path))
    for org in orgs:
        orgPath = os.path.join(path, org)

        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml")  # namespace.yaml
        caYaml = os.path.join(orgPath, org + "-ca.yaml")  # ca.yaml
        cliYaml = os.path.join(orgPath, org + "-cli.yaml")  # cli.yaml

        for peer in sorted(os.listdir(orgPath + "/peers")):
            peerPath = os.path.join(orgPath + "/peers", peer)
            peerYaml = os.path.join(peerPath, peer + ".yaml")
            checkAndDelete(peerYaml)

        checkAndDelete(cliYaml)
        checkAndDelete(caYaml)
        checkAndDelete(namespaceYaml)


def deleteKafkas(path):
    for i in range(0, 4):
        kafkaYaml = os.path.join(path, "kafka" + str(i) + "-kafka.yaml")
        checkAndDelete(kafkaYaml)

    for i in range(0, 3):
        zkYaml = os.path.join(path, "zookeeper" + str(i) + "-zookeeper.yaml")
        checkAndDelete(zkYaml)

    namespaceYaml = os.path.join(path, "kafka-namespace.yaml")
    checkAndDelete(namespaceYaml)


def checkAndDelete(f):
    if os.path.isfile(f):
        os.system("kubectl delete -f " + f)


if __name__ == "__main__":
    deletePeers(PEER)
    deleteOrderers(ORDERER)
    deleteKafkas(KAFKA)
