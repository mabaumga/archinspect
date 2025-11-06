Feature: Repository Import
  As a system administrator
  I want to import repositories from a CSV file
  So that I can manage them in the application

  Scenario: Import repositories from CSV
    Given a CSV file with repository data
    When I run the import command
    Then repositories should be created in the database
    And each repository should have correct attributes

  Scenario: Import is idempotent
    Given a CSV file with repository data
    And repositories have been imported once
    When I run the import command again
    Then no duplicate repositories should be created
