Feature: Management of application by the manager

  Background:
    Given The manager is logged
    And Go to assistant home page

  Scenario: Edit administrative data of an assistant
    When Click on dashboard link
    Then Click randomly on edit assistant link
    Then Edit assistant administrative data