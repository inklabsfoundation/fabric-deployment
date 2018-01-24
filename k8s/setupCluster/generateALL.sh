#!/bin/bash +x

EXPORTS=$4
: ${EXPORTS:=""}
NFS=$3
: ${NFS:=""}
ALL_VOLUMES=$2
: ${ALL_VOLUMES:=""}
EXTEND=$1
: ${EXTEND:=false}

export TOOLS=$PWD/../bin
export CONFIG_PATH=$PWD
export FABRIC_CFG_PATH=$PWD


## Generates Org certs
function generateCerts (){
	CRYPTOGEN=$TOOLS/cryptogen
    if $EXTEND; then
        $CRYPTOGEN extend --input=crypto-config --config=./cluster-config.yaml
    else
	    $CRYPTOGEN generate --config=./cluster-config.yaml
	fi

}

function generateChannelArtifacts() {
    if $EXTEND; then
        return
    fi

	if [ ! -d channel-artifacts ]; then
		mkdir channel-artifacts
	fi


	CONFIGTXGEN=$TOOLS/configtxgen
 	$CONFIGTXGEN -profile TwoOrgsOrdererGenesis -outputBlock ./channel-artifacts/genesis.block
# 	$CONFIGTXGEN -profile TwoOrgsChannel -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID $CHANNEL_NAME
#	$CONFIGTXGEN -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID $CHANNEL_NAME -asOrg Org1MSP
# 	$CONFIGTXGEN -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID $CHANNEL_NAME -asOrg Org2MSP
# 	$CONFIGTXGEN -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org3MSPanchors.tx -channelID $CHANNEL_NAME -asOrg Org3MSP
	
	chmod -R 777 ./channel-artifacts && chmod -R 777 ./crypto-config

	cp ./channel-artifacts/genesis.block ./crypto-config/ordererOrganizations/*

	cp -r ./crypto-config /opt/share/ && cp -r ./channel-artifacts /opt/share/
	#/opt/share mouts the remote /opt/share from nfs server
}

function generateKafkaDir() {
    if $EXTEND; then
        return
    fi

    if [ ! -d ./crypto-config/kafka ]; then
        mkdir -p ./crypto-config/kafka
    fi
}

function generateK8sYaml (){
    if $EXTEND; then
	    python3 transform/generate.py -v $ALL_VOLUMES -n $NFS -p $EXPORTS
    else
        python3 transform/generate.py -o -v $ALL_VOLUMES -n $NFS
    fi
}

function clean () {
    if ! $EXTEND; then
	    rm -rf /opt/share/crypto-config/*
	    rm -rf crypto-config
    fi
}

function extend() {
    if $EXTEND; then
        rsync -rv --exclude=*.yaml --ignore-existing ./crypto-config /opt/share/
        rmdir /opt/share/crypto-config/kafka
    fi

}

## Genrates orderer genesis block, channel configuration transaction and anchor peer upddate transactions
##function generateChannelArtifacts () {
##	CONFIGTXGEN=$TOOLS/configtxgen

#}
clean
generateCerts
generateChannelArtifacts
generateKafkaDir
generateK8sYaml
extend