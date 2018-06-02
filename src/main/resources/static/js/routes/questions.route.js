'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/questions', {
      templateUrl: 'templates/questions.html',
      controller: 'QuestionsCtrl',
      activeTab: 'questions',
      resolve: {
        questions: function($rootScope, $q, Question) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Question.all().query(function(questions) {
            deferred.resolve(questions);
          });
          return deferred.promise;
        }
      }
    });
  });
