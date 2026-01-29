// Hearings AI - Azure Infrastructure
// Deploys all required Azure resources for the Hearings AI POC

targetScope = 'resourceGroup'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'hearingsai'

@description('Azure AD tenant ID for authentication')
param tenantId string

@description('Azure AD client ID for the application')
param clientId string

// Generate unique suffix for globally unique names
var uniqueSuffix = uniqueString(resourceGroup().id)
var resourcePrefix = '${baseName}-${environment}'
// Shorter suffix for storage account (max 24 chars)
var shortSuffix = substring(uniqueSuffix, 0, 8)

// === Azure OpenAI ===
// Deployed to East US because text-embedding-3-large is not available in Canada Central
// Note: Embeddings are processed (not stored), so this doesn't violate data residency requirements
module openai 'modules/openai.bicep' = {
  name: 'openai-deployment'
  params: {
    name: '${resourcePrefix}-oai-${shortSuffix}'
    location: 'eastus'
    deployments: [
      {
        name: 'gpt-4o'
        model: 'gpt-4o'
        version: '2024-08-06'
        sku: 'GlobalStandard'
        capacity: 30
      }
      {
        name: 'text-embedding-3-large'
        model: 'text-embedding-3-large'
        version: '1'
        sku: 'Standard'
        capacity: 120
      }
    ]
  }
}

// === Azure AI Search ===
module search 'modules/ai-search.bicep' = {
  name: 'search-deployment'
  params: {
    name: '${resourcePrefix}-srch-${shortSuffix}'
    location: location
    sku: environment == 'prod' ? 'standard' : 'basic'
    replicaCount: environment == 'prod' ? 2 : 1
    partitionCount: 1
    semanticSearch: 'standard'
  }
}

// === Cosmos DB ===
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos-deployment'
  params: {
    name: '${resourcePrefix}-db-${shortSuffix}'
    location: location
    databaseName: 'hearings'
    containers: [
      {
        name: 'documents'
        partitionKey: '/proceedingId'
      }
      {
        name: 'proceedings'
        partitionKey: '/id'
      }
      {
        name: 'audit'
        partitionKey: '/userId'
        ttlSeconds: 7776000 // 90 days
      }
    ]
  }
}

// === Storage Account ===
module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    name: 'hearingsai${shortSuffix}'
    location: location
    containers: [
      'hearing-documents'
      'processed-chunks'
    ]
  }
}

// === Container Apps Environment ===
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${resourcePrefix}-env'
  location: location
  properties: {
    zoneRedundant: environment == 'prod'
  }
}

// === Container App (API) ===
resource apiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${resourcePrefix}-api'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: environment == 'prod' ? ['https://${resourcePrefix}-web.azurestaticapps.net'] : ['http://localhost:3000', 'http://localhost:5173']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      secrets: [
        {
          name: 'openai-endpoint'
          value: openai.outputs.endpoint
        }
        {
          name: 'search-endpoint'
          value: search.outputs.endpoint
        }
        {
          name: 'cosmos-endpoint'
          value: cosmos.outputs.endpoint
        }
        {
          name: 'storage-endpoint'
          value: storage.outputs.blobEndpoint
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'AZURE_OPENAI_ENDPOINT', secretRef: 'openai-endpoint' }
            { name: 'AZURE_OPENAI_DEPLOYMENT_CHAT', value: 'gpt-4o' }
            { name: 'AZURE_OPENAI_DEPLOYMENT_EMBEDDING', value: 'text-embedding-3-large' }
            { name: 'AZURE_SEARCH_ENDPOINT', secretRef: 'search-endpoint' }
            { name: 'AZURE_SEARCH_INDEX', value: 'hearings-index' }
            { name: 'COSMOS_ENDPOINT', secretRef: 'cosmos-endpoint' }
            { name: 'COSMOS_DATABASE', value: 'hearings' }
            { name: 'STORAGE_ACCOUNT_URL', secretRef: 'storage-endpoint' }
            { name: 'STORAGE_CONTAINER', value: 'hearing-documents' }
            { name: 'AZURE_TENANT_ID', value: tenantId }
            { name: 'AZURE_CLIENT_ID', value: clientId }
            { name: 'ENVIRONMENT', value: environment }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 0
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// === Role Assignments ===

// API -> OpenAI: Cognitive Services OpenAI User
resource openaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, apiApp.name, 'Cognitive Services OpenAI User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// API -> Search: Search Index Data Contributor
resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, apiApp.name, 'Search Index Data Contributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// API -> Storage: Storage Blob Data Contributor
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, apiApp.name, 'Storage Blob Data Contributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// === Outputs ===
output apiEndpoint string = 'https://${apiApp.properties.configuration.ingress.fqdn}'
output openaiEndpoint string = openai.outputs.endpoint
output searchEndpoint string = search.outputs.endpoint
output cosmosEndpoint string = cosmos.outputs.endpoint
output storageEndpoint string = storage.outputs.blobEndpoint
output apiPrincipalId string = apiApp.identity.principalId
