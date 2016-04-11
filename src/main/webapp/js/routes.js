'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'templates/home.html',
        controller: 'HomeCtrl',
        activeTab: 'home'
      })
      .when('/bets', {
        templateUrl: 'templates/bets.html',
        controller: 'BetsCtrl',
        activeTab: 'bets'
      })
      .when('/ladder', {
        templateUrl: 'templates/ladder.html',
        controller: 'LadderCtrl',
        activeTab: 'ladder'
      })
      .when('/questions', {
        templateUrl: 'templates/questions.html',
        controller: 'QuestionsCtrl',
        activeTab: 'questions'
      })
      .when('/rules', {
        templateUrl: 'templates/rules.html',
        controller: 'RulesCtrl',
        activeTab: 'rules'
      })
      .when('/shoutbox', {
        templateUrl: 'templates/shoutbox.html',
        controller: 'ShoutboxCtrl',
        activeTab: 'shoutbox'
      })
      .when('/login', {
        templateUrl: 'templates/login.html',
        controller: 'LoginCtrl',
        activeTab: 'login'
      })
      .when('/admin', {
        templateUrl: 'templates/admin.html',
        controller: 'AdminCtrl',
        activeTab: 'admin'
      })
      .otherwise({
        redirectTo: '/'
      });
  });
