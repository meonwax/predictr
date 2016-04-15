'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    var checkAuthentication = function($q, Authentication) {
      if (Authentication.getToken()) {
        return $q.when();
      } else {
        return $q.reject();
      }
    };
    $routeProvider
      .when('/login', {
        templateUrl: 'templates/login.html',
        controller: 'LoginCtrl',
        activeTab: 'login'
      })
      .when('/', {
        templateUrl: 'templates/home.html',
        controller: 'HomeCtrl',
        activeTab: 'home',
        resolve: {auth: checkAuthentication}
      })
      .when('/bets', {
        templateUrl: 'templates/bets.html',
        controller: 'BetsCtrl',
        activeTab: 'bets',
        resolve: {auth: checkAuthentication}
      })
      .when('/ladder', {
        templateUrl: 'templates/ladder.html',
        controller: 'LadderCtrl',
        activeTab: 'ladder',
        resolve: {auth: checkAuthentication}
      })
      .when('/questions', {
        templateUrl: 'templates/questions.html',
        controller: 'QuestionsCtrl',
        activeTab: 'questions',
        resolve: {auth: checkAuthentication}
      })
      .when('/rules', {
        templateUrl: 'templates/rules.html',
        controller: 'RulesCtrl',
        activeTab: 'rules',
        resolve: {auth: checkAuthentication}
      })
      .when('/shoutbox', {
        templateUrl: 'templates/shoutbox.html',
        controller: 'ShoutboxCtrl',
        activeTab: 'shoutbox',
        resolve: {auth: checkAuthentication}
      })
      .when('/admin', {
        templateUrl: 'templates/admin.html',
        controller: 'AdminCtrl',
        activeTab: 'admin',
        resolve: {auth: checkAuthentication}
      })
      .otherwise({
        redirectTo: '/'
      });
  });
