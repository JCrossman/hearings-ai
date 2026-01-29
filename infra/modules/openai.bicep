// Azure OpenAI module for Hearings AI

@description('Name of the OpenAI resource')
param name string

@description('Azure region')
param location string

@description('Model deployments')
param deployments array = []

resource openai 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: name
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = [for dep in deployments: {
  parent: openai
  name: dep.name
  sku: {
    name: dep.?sku ?? 'GlobalStandard'
    capacity: dep.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: dep.model
      version: dep.version
    }
  }
}]

output id string = openai.id
output name string = openai.name
output endpoint string = openai.properties.endpoint
