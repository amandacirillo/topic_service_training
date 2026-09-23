/**
 * Resolves per-environment configuration from a short environment name.
 *
 * A real deploy pipeline determines this name from a parsed git tag (e.g.
 * `deploy-stg-2024.03.1`) rather than a hardcoded map like this training
 * example uses -- but "one small config object per environment, looked up
 * by name" is the reusable part.
 */
export interface EnvironmentConfig {
  name: string;
  account: string;
  region: string;
  desiredCount: number;
  cpu: number;
  memoryMiB: number;
  apiKeySecretName: string;
}

const ENVIRONMENTS: Record<string, EnvironmentConfig> = {
  dev: {
    name: 'dev',
    account: '111111111111',
    region: 'us-east-1',
    desiredCount: 1,
    cpu: 256,
    memoryMiB: 512,
    apiKeySecretName: 'topic-service/dev/api-key',
  },
  stg: {
    name: 'stg',
    account: '222222222222',
    region: 'us-east-1',
    desiredCount: 1,
    cpu: 256,
    memoryMiB: 512,
    apiKeySecretName: 'topic-service/stg/api-key',
  },
  prd: {
    name: 'prd',
    account: '333333333333',
    region: 'us-east-1',
    desiredCount: 2,
    cpu: 512,
    memoryMiB: 1024,
    apiKeySecretName: 'topic-service/prd/api-key',
  },
};

export function resolveEnvironment(name: string): EnvironmentConfig {
  const config = ENVIRONMENTS[name];
  if (!config) {
    throw new Error(`Unknown environment '${name}'. Valid options: ${Object.keys(ENVIRONMENTS).join(', ')}`);
  }
  return config;
}
