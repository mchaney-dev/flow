## Contributing
To contribute, [look at open issues](https://github.com/mchaney-dev/flow/issues), fork the repository and open a pull request with your changes. If you experience a bug or would like a feature to be added, please feel free to open an issue.

### Environment Setup
This project is developed using Google Cloud Functions, Firestore, and Postman.
#### Google Cloud
These instructions will describe deployment with the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), as it makes development and testing easier. To set up and deploy services in Google Cloud:
1. Make sure you cloned this Github repository locally.
2. Open the Google Cloud CLI, log in and create a new project (make sure there is a billing account associated with your new project, or it won't work).
3. Using the CLI, navigate to the location of the cloned repository on your machine.
4. Run `gcloud functions deploy [SERVICE_FOLDER] --runtime python310 --trigger-http --allow-unauthenticated --entry-point request_handler`.
`[SERVICE_FOLDER]` is the location of files relating to a service inside the repository, e.g. `./services/user`.
5. Save the URL that `gcloud` generates for you at deployment. The output should be something like:
```
buildConfig: ...
createTime: ...
...
state: ...
updateTime: ...
url: https://[REGION]-[PROJECT].cloudfunctions.net/[FUNCTION]
```
You will need this URL for later testing.

#### Firestore
Create a Firestore database inside the [Google Cloud Console](https://console.cloud.google.com). Make sure it is a **Native** database attached to the Google Cloud project you created earlier.

#### Postman
[Import the API specification](https://learning.postman.com/docs/design-apis/specifications/import-a-specification/) for the service(s) you want to contribute to. Configure your `baseUrl` to be the URL you saved earlier. You are now ready to test API calls from Postman.