# `omnivore-rss-handler-hack`

Hack to subscribe RSS feeds on a self-hosted Omnivore instance.

Currently, Omnivore's RSS subscriptions rely on cloud tasks. Therefore, self-hosted instances miss this feature.  This repo provides a simple Python script, which reads the `FEEDS_FILE` (JSON), iterates over its entries, [parses their feeds](https://feedparser.readthedocs.io/en/latest/#), and [tells Omnivore to add new articles](https://docs.omnivore.app/integrations/api.html#saving-a-url-with-the-api). To avoid re-adding articles, it uses a `CACHE_FILE` (JSON) to remember which articles were already added. Scheduling this script ([e.g., using a cron job](#example-kubernetes-cron-job-to-schedule-omnivore-rss-handler-hack)) once an hour mimics (hosted) Omnivores' built-in support for RSS subscriptions.


## `FEEDS_FILE` Structure

```json
{
  "blog": "https://blog.example/feed",
  "another-blog": "https://another-blog.example/rss.xml",
}
```

## Build and Push Image

(If you trust me, you can use mine on Docker Hub: `sejaeger/omnivore-rss-handler-hack`)

```bash 
docker build -t <Your Docker Hub User>/omnivore-rss-handler-hack:v0.1 .
docker push <Your Docker Hub User>/omnivore-rss-handler-hack:v0.1
```


## Example Kubernetes Cron-Job to Schedule `omnivore-rss-handler-hack`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  namespace: omnivore
  name: omnivore-rss-handler-hack
spec:
  # run hourly
  schedule: "*/60 * * * *"
  failedJobsHistoryLimit: 1
  successfulJobsHistoryLimit: 3
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: dyndns-updater
              image: <Your Docker Hub User>/omnivore-rss-handler-hack:v0.1
              imagePullPolicy: IfNotPresent
              env:
                # This is the internal URL, you can also use a public URL
                - name: API_URL
                  value: "http://omnivore-omnivore-api:8080/api/graphql"
                # Somehow inject your Omnivore API token: https://docs.omnivore.app/integrations/api.html#getting-an-api-token
                - name: API_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: omnivore-api-token
                      key: API_TOKEN
                - name: CACHE_FILE
                  value: "/home/cache.json"
                - name: FEEDS_FILE
                  value: "/home/feeds.json"
              volumeMounts:
                - name: cache-feed-directory
                  mountPath: /home
          volumes:
            - name: cache-feed-directory
              persistentVolumeClaim:
                claimName: omnivore-pvc
```
