Feature: API Integration Tests
  As an API client
  I want to verify all endpoints work correctly
  So that I know the API is functioning properly

  # Authentication and Authorization with Sample GET API
  
  Scenario: Access protected endpoint with valid token
    Given I have acquired a valid token with required role
    When I send a GET request to "/sample"
    Then the response status code is 200
    And the response body contains a message
    And the response contains a correlation ID header

  Scenario: Access protected endpoint without authorization header
    Given I have no authorization header
    When I send a GET request to "/sample"
    Then the response indicates an authentication error

