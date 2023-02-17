#!/usr/bin/env python

import os
import boto3

def configure_aws(config):
    aws = config['aws']
    key = aws['aws_access_key_id']
    secret = aws['aws_secret_access_key']
    awsdir = os.path.expanduser('~/.aws')
    if not os.path.exists(awsdir):
        os.makedirs(awsdir)
    cred = f'''[default]
aws_access_key_id = {key}
aws_secret_access_key = {secret}
'''
    with open(f'{awsdir}/credentials', 'w') as f:
        f.write(cred)

def add_cname_record(config, source):
    host = config['host']['name']
    zoneid = config['host']['zoneid']
    domain = config['host']['domain']
    dest = f'{host}.{domain}'

    try:
        client = boto3.client('route53')
        print(f'adding {source} => {dest}')
        rc = client.change_resource_record_sets(
            HostedZoneId = zoneid,
            ChangeBatch = {
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': f'{source}.{domain}',
                            'Type': 'CNAME',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': dest}]
                        }
                    }
                ]
            })
        print('cname:', rc)
    except Exception as e:
        print('exception adding cname:', e)

def remove_cname_record(config, source):
    host = config['host']['name']
    zoneid = config['host']['zoneid']
    domain = config['host']['domain']
    dest = f'{host}.{domain}'

    try:
        client = boto3.client('route53')
        print(f'removing {source} => {dest}')
        rc = client.change_resource_record_sets(
            HostedZoneId = zoneid,
            ChangeBatch = {
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': f'{source}.{domain}',
                            'Type': 'CNAME',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': dest}]
                        }
                    }
                ]
            })
        print('cname:', rc)
    except Exception as e:
        print('exception removing cname:', e)
