# Bot Detection Service

In the gaming industry, detecting cheaters is crucial for maintaining a fair and competitive environment. This bot detection service leverages a machine learning model to analyze player behavior in real-time, identifying patterns indicative of bot and cheater activity. By consuming telemetry data from game sessions, applying feature extraction techniques, and utilizing a pre-trained model, this service can flag potential cheaters. This solution can enhance the integrity of your game, ensuring a level playing field for all players and improving overall user experience. This service is particularly beneficial for online multiplayer games where cheating can significantly impact the game's balance and player satisfaction.

This service consumes data from a topic, applies a bot detection model, and publishes the result of the model to an output topic.

## Environment Variables

The code sample uses the following environment variables:

- **input**: Name of the input topic to listen to.
- **output**: Name of the output topic to write to.
- **AWS_SECRET_ACCESS_KEY**: Your AWS secret access key.
- **AWS_ACCESS_KEY_ID**: Your AWS access key ID.

## Dockerfile

The Dockerfile sets up the environment and dependencies for the bot detection service.

## Contribute

Submit forked projects to the Quix [GitHub](https://github.com/quixio/quix-samples) repo. Any new project that we accept will be attributed to you and you'll receive $200 in Quix credit.

## Open source

This project is open source under the Apache 2.0 license and available in our [GitHub](https://github.com/quixio/quix-samples) repo.

Please star us and mention us on social to show your appreciation.