import { App } from 'aws-cdk-lib';
import { TopicServiceStack } from '../lib/stack';
import { resolveEnvironment } from '../lib/environment';

const app = new App();

// The environment (dev/stg/prd) is resolved from a deploy-time tag/branch
// name in the real pipeline, not hardcoded here -- see lib/environment.ts
// and the repo README's "Tag-driven deploys" section for the pattern.
const env = resolveEnvironment(process.env.DEPLOY_ENV_NAME ?? 'dev');

new TopicServiceStack(app, `TopicService-${env.name}`, {
  env: { region: env.region, account: env.account },
  envConfig: env,
});
