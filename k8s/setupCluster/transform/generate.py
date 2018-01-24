import os

import config as tc
import argparse

BASEDIR = os.path.dirname(__file__)
ORDERER = os.path.join(BASEDIR, "../crypto-config/ordererOrganizations")
PEER = os.path.join(BASEDIR, "../crypto-config/peerOrganizations")
KAFKA = os.path.join(BASEDIR, "../crypto-config/kafka")


# generateNamespacePod generate the yaml file to create the namespace for k8s, and return a set of paths which indicate the location of org files

def generateKafka(DIR, override, all_volumes):
    tc.configKafkaNamespace(DIR, override)
    tc.configZookeepers(DIR, override, all_volumes)
    tc.configKafkas(DIR, override, all_volumes)


def generateNamespacePod(DIR, override, all_volumes, nfs, ex_ports):
    orderer0 = sorted(os.listdir(ORDERER))[0]
    orgs = []
    for index, org in enumerate(sorted(os.listdir(DIR))):
        orgDIR = os.path.join(DIR, org)
        ## generate namespace first.
        tc.configORGS(org, orgDIR, orderer0, override, index, all_volumes, nfs, ex_ports)
        orgs.append(orgDIR)
    # orgs.append(orgDIR + "/" + DIR.lower())

    # print(orgs)
    return orgs


def generateDeploymentPod(orgs, override, all_volumes, ex_ports):
    for orgindex, org in enumerate(orgs):

        if org.find("peer") != -1:  # whether it create orderer pod or peer pod
            suffix = "/peers"
        else:
            suffix = "/orderers"

        members = sorted(os.listdir(org + suffix))
        for nodeindex, member in enumerate(members):
            print(member)
            memberDIR = os.path.join(org + suffix, member)
            # print(memberDIR)
            # print(os.listdir(memberDIR))
            tc.generateYaml(member, memberDIR, suffix, override, orgindex, nodeindex, all_volumes, ex_ports)


def allInOne():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--override", action="store_true", help="Override existing k8s yaml files")
    parser.add_argument("-v", "--volumes", help="Persistent volumes list")
    parser.add_argument("-n", "--nfs", help="nfs server address")
    parser.add_argument("-p", "--exports", help="ex ports for orgs")
    args = parser.parse_args()
    all_volumes = {"zk_log": [], "zk_data": [], "kafka": [], "ca": [], "orderer": [], "peer": []}
    if args.volumes and args.volumes != "":
        volumes = args.volumes.split(";")
        for sub_volumes in volumes:
            key = sub_volumes.split(":")[0]
            value = sub_volumes.split(":")[1]
            if key == "zk_log" or key == "zk_data" or key == "kafka":
                values = value.split(",")
                all_volumes[key] = values
            else:
                values = value.split("*")
                for sub_value in values:
                    sub_values = sub_value.split(",")
                    all_volumes[key].append(sub_values)
    ex_ports = {"ca": [], "orderer": [], "peer": []}
    print(args.exports)
    if args.exports and args.exports != "":
        ports = args.exports.split(";")
        for sub_ports in ports:
            key = sub_ports.split(":")[0]
            value = sub_ports.split(":")[1]
            values = value.split(",")
            ex_ports[key] = values
    print(all_volumes)
    print(ex_ports)
    if args.override:
        if not args.nfs:
            exit(2)

    peerOrgs = generateNamespacePod(PEER, args.override, all_volumes, args.nfs, ex_ports)
    generateDeploymentPod(peerOrgs, args.override, all_volumes, ex_ports)

    generateKafka(KAFKA, args.override, all_volumes)
    ordererOrgs = generateNamespacePod(ORDERER, args.override, all_volumes, args.nfs, ex_ports)
    generateDeploymentPod(ordererOrgs, args.override, all_volumes, ex_ports)


if __name__ == "__main__":
    allInOne()
