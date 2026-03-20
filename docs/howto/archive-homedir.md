- aws access to the cluster


Create a bucket in S3:
aws s3 s3://jmte-prod-homedirs-archive --region us-west-2
aws s3 ls


Create a role with no permissions:
aws iam get-role --role-name homedirs-archive-access


Create a policy that can write into that bucket, and attach it to the role we just created:

aws iam put-role-policy --role-name homedirs-archive-access --policy-name HomedirsArchiveAccess_policy --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":["arn:aws:s3:::jmte-prod-homedirs-archive","arn:aws:s3:::jmte-prod-homedirs-archive/*"]}]}'


python3 archive-home-dirs.py \
    --archive-name="archive-$(date +'%Y-%m-%d')" \
    --basedir=/home/jovyan/allusers/ \
    --bucket-name=jmte-prod-homedirs-archive \
    --object-prefix="archives/" \
    --usernames-file=to_archive.txt \
    --temp-path=/home/jovyan/archive-staging/