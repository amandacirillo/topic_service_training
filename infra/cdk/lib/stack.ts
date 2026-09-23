import { Stack, StackProps, Duration, RemovalPolicy } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { EnvironmentConfig } from './environment';

export interface TopicServiceStackProps extends StackProps {
  envConfig: EnvironmentConfig;
}

/**
 * A minimal ECS Fargate + RDS Postgres deployment, fronted by an
 * application load balancer. This mirrors the shape of the real service's
 * deploy pipeline (build image -> push to ECR -> deploy to ECS by
 * environment) without any environment-specific resource IDs.
 */
export class TopicServiceStack extends Stack {
  constructor(scope: Construct, id: string, props: TopicServiceStackProps) {
    super(scope, id, props);

    const { envConfig } = props;

    const vpc = new ec2.Vpc(this, 'Vpc', { maxAzs: 2, natGateways: 1 });

    const apiKeySecret = secretsmanager.Secret.fromSecretNameV2(
      this, 'ApiKeySecret', envConfig.apiKeySecretName
    );

    const database = new rds.DatabaseInstance(this, 'Database', {
      vpc,
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
      allocatedStorage: 20,
      removalPolicy: envConfig.name === 'prd' ? RemovalPolicy.SNAPSHOT : RemovalPolicy.DESTROY,
      credentials: rds.Credentials.fromGeneratedSecret('topic_service'),
    });

    const cluster = new ecs.Cluster(this, 'Cluster', {
      vpc,
      clusterName: `topic-service-${envConfig.name}`,
    });

    const service = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'Service', {
      cluster,
      serviceName: `topic-service-${envConfig.name}`,
      cpu: envConfig.cpu,
      memoryLimitMiB: envConfig.memoryMiB,
      desiredCount: envConfig.desiredCount,
      taskImageOptions: {
        image: ecs.ContainerImage.fromAsset('../../'),
        containerPort: 5000,
        environment: {
          FLASK_DEBUG: 'false',
        },
        secrets: {
          API_KEY: ecs.Secret.fromSecretsManager(apiKeySecret),
          DATABASE_URL: ecs.Secret.fromSecretsManager(database.secret!, 'connectionString'),
        },
      },
      healthCheckGracePeriod: Duration.seconds(60),
    });

    service.targetGroup.configureHealthCheck({ path: '/healthz' });
    database.connections.allowDefaultPortFrom(service.service);
  }
}
