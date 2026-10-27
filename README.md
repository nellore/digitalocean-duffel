# Duffel

Duffel creates permalinks to real locations of data resources and logs accesses. It is used by recount2 and was originally hosted on webfaction using the code at https://github.com/nellore/duffel. After webfaction was eaten by godaddy, the host was switched to digitalocean. This is a fork of the digitalocean sample Flask app incorporating Duffel's code. The sample Flask app's readme is below.

## What Duffel logs (privacy)

Duffel exists to create permalinks and to report *aggregate* usage of recount2/recount3. It is designed not to store anything that identifies a person or machine:

* **No IP addresses.** Each log line carries a pseudonym: HMAC-SHA256 of the client IP, keyed with a secret that lives only on the server (`~/recount2_logs/duffel_secret`, created automatically with mode 600, or the `DUFFEL_LOG_SECRET` environment variable). The secret is never committed. Without it, pseudonyms cannot be matched against candidate IPs.
* **Yearly rotation.** The secret is mixed with the calendar year, so a pseudonym is stable within a year (enabling unique visitors per day/week/month/year) but cannot be linked across years.
* **Date only.** Lines record the UTC date, never the time of day.
* **No probe strings.** Only requests that resolve to a real file have their path logged; everything else is logged with `-` in place of the path.
* **Retention.** Set `DUFFEL_LOG_RETENTION_DAYS=N` to delete log files older than N days at startup (default: keep all).

Log line format:

    YYYY-MM-DD [TAB] pseudonym [TAB] resource [TAB] path

To compute hits and unique visitors (standard library only):

    python analytics.py --by month ~/recount2_logs/recount_log.*.tsv.gz
    python analytics.py --by year ~/recount2_logs/recount_log.*.tsv.gz
    python analytics.py --by day --resource recount3 ~/recount2_logs/recount_log.*.tsv.gz

Deleting `duffel_secret` makes every existing pseudonym permanently unmatchable; do this if the logs are ever shared beyond the maintainers.

# Getting Started #

These steps will get this sample Flask application running for you using DigitalOcean.

**Note: Following these steps will result in charges for the use of DigitalOcean services**

## Requirements

* You need a DigitalOcean account. If you don't already have one, you can sign up at https://cloud.digitalocean.com/registrations/new
    
## Forking the Sample App Source Code

To use all the features of App Platform, you need to be running against your own copy of this application. To make a copy, click the Fork button above and follow the on-screen instructions. In this case, you'll be forking this repo as a starting point for your own app (see [Github documentation](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) to learn more about forking repos.

After forking the repo, you should now be viewing this README in your own github org (e.g. `https://github.com/<your-org>/sample-flask`)

## Deploying the App ##

1. Visit https://cloud.digitalocean.com/apps (if you're not logged in, you may see an error message. Visit https://cloud.digitalocean.com/login directly and authenticate, then try again)
1. Click "Launch App" or "Create App"
1. Choose GitHub and authenticate with your GitHub credentials.
1. Under Repository, choose this repository (e.g. `<your-org>/sample-flask`) and click **Next**.
1. On the next screen you will be prompted for the name of your app, which region you wish to deploy to, which branch you want deployments to spin off of and whether or not you wish to autodeploy the app every time an update is made to this branch. Fill this out according to how you want your app to function and click **Next**.
1. Modify the **Run Command** setting to point to your application. For this example my project is named `mysite`. So the modified command would be `gunicorn --worker-tmp-dir /dev/shm --config gunicorn_config.py app:app`. 
1. There is no need to modify the **Build Command** section
1. Confirm your Plan settings and how many containers you want to launch and click **Launch Basic/Pro App**.
1. You should see a "Building..." progress indicator. And you can click "Deployments"→"Details" to see more details of the build.
1. It can currently take 5-6 minutes to build this app, so please be patient. Live build logs are coming soon to provide much more feedback during deployments.
1. Once the build completes successfully, click the "Live App" link in the header and you should see your running application in a new tab, displaying the home page.

## Making Changes to Your App ##

As long as you left the default Autodeploy option enabled when you first launched this app, you can now make code changes and see them automatically reflected in your live application. During these automatic deployments, your application will never pause or stop serving request because the App Platform offers zero-downtime deployments.

Here's an example code change you can make for this app:
1. Edit code within the repository
1. Commit the change to master. Normally it's a better practice to create a new branch for your change and then merge that branch to master after review, but for this demo you can commit to master directly.
1. Visit https://cloud.digitalocean.com/apps and navigate to your sample-python app.
1. You should see a "Building..." progress indicator, just like above.
1. Once the build completes successfully, click the "Live App" link in the header and you should see your updated application running. You may need to force refresh the page in your browser (e.g. using Shift+Reload).

## Learn More ##

You can learn more about the App Platform and how to manage and update your application at https://www.digitalocean.com/docs/apps/.


## Deleting the App #

When you no longer need this sample application running live, you can delete it by following these steps:
1. Visit the Apps control panel at https://cloud.digitalocean.com/apps
1. Navigate to the sample-python app
1. Choose "Settings"->"Destroy"

This will delete the app and destroy any underlying DigitalOcean resources

**Note: If you don't delete your app, charges for the use of DigitalOcean services will continue to accrue.**
