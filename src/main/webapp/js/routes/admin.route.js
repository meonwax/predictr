'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/admin', {
      templateUrl: 'templates/admin.html',
      controller: 'AdminCtrl',
      activeTab: 'admin',
      resolve: {
        games: function($rootScope, $q, Game) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Game.all().query(function(games) {
            deferred.resolve(games);
          });
          return deferred.promise;
        },
        teams: function($rootScope, $q, Team) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Team.query(function(teams) {
            deferred.resolve(teams);
          });
          return deferred.promise;
        },
        questions: function($rootScope, $q, Question) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Question.all().query(function(questions) {
            deferred.resolve(questions);
          });
          return deferred.promise;
        },
        users: function($rootScope, $q, User) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          User.all().query(function(users) {
            deferred.resolve(users);
          });
          return deferred.promise;
        }
      }
    });
  });
