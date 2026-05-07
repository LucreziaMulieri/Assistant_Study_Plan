# Assistant_Study_Plan
Project related to the creation of a web application that allows the use of a bot created using Amazon Lex.

The services used to build it, in addition to Amazon Lex, are other services 
provided by Amazon Web Services. These include:

- **Amazon Lambda**: used to create Lambda functions to handle specific aspects 
  of the conversation with the user that cannot be directly implemented using 
  only the tools provided by Lex.
- **Amazon CloudWatch**: used to manage the deployment of the created Lambda 
  functions, as well as to accurately understand the bot's conversation flow 
  and the correct integration of the Lambda Functions.
- **Amazon IAM**: for managing permissions within the functions themselves.
- **Amazon DynamoDB**: enabled the creation of a NoSQL database, where data 
  related to the optional courses offered by the Università Politecnica delle 
  Marche was stored, with the intent of retrieving it during the conversation 
  with the user to provide more detailed information about the courses.
- **Amazon CloudShell**: for managing terminal commands, allowing the creation 
  of the DynamoDB database and the web application, leveraging sample templates 
  already provided by Amazon Web Services (further information can be found in 
  the Amazon documentation), modified for this specific use case.
- **Amazon CloudFormation**: for managing the deployment of the entire 
  infrastructure, with the ability to create a template specifying all the 
  services used along with their configurations, enabling automatic deployment.

  <img width="2813" height="1625" alt="architettura" src="https://github.com/user-attachments/assets/2ece72b8-ab74-4add-a69b-f53b5e1c5d2e" />

  Specifically, three Lambda functions were created: one to provide additional information about a specific course specified by the user, for example, if the user wishes to know the syllabus for a particular course; the second to
provide a list of courses related to the user's choices, attempting to target them based on their area of ​​interest, for example, automation courses rather than computer science courses; the last is a handler that allows the other two to be
dynamically called at points of interest in the conversation.

## Demo

Try the chatbot at the following link:  
[Study Plan Assistant](https://dw5yknl67tidn.cloudfront.net/index.html)

## References & Credits

- [aws-lex-web-ui](https://github.com/aws-samples/aws-lex-web-ui) — Sample project 
  provided by Amazon Web Services for deploying a web interface for an Amazon Lex chatbot. 
  The template was adapted and modified for this specific use case.
- [Deploy a web UI for your chatbot](https://aws.amazon.com/it/blogs/machine-learning/deploy-a-web-ui-for-your-chatbot/) — 
  Official AWS Machine Learning blog post used as a reference guide for the 
  deployment of the web interface.

