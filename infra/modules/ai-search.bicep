// Azure AI Search module for Hearings AI

@description('Name of the search service')
param name string

@description('Azure region')
param location string

@description('SKU for the search service')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

@description('Number of replicas')
param replicaCount int = 1

@description('Number of partitions')
param partitionCount int = 1

@description('Semantic search tier')
@allowed(['disabled', 'free', 'standard'])
param semanticSearch string = 'standard'

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    semanticSearch: semanticSearch
    publicNetworkAccess: 'enabled'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

output id string = searchService.id
output name string = searchService.name
output endpoint string = 'https://${searchService.name}.search.windows.net'
