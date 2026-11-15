from django.contrib import admin

from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz, QuizQuestion


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0
    fields = ("title", "summary", "position")


class LessonInline(admin.TabularInline):
    model = Lesson
    fk_name = "module"
    extra = 0
    fields = ("title", "kind", "position", "estimated_minutes", "xp", "is_published")


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "position", "is_published", "course_count")
    list_filter = ("level", "is_published")
    search_fields = ("title", "description")
    ordering = ("position", "title")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="courses")
    def course_count(self, obj):
        return obj.courses.count()


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseModuleInline]
    list_display = ("title", "level", "category", "learning_path", "instructor", "enrolled_count", "position",
                    "is_published")
    list_filter = ("is_published", "level", "category", "learning_path")
    search_fields = ("title", "subtitle", "description")
    list_select_related = ("learning_path", "instructor")
    ordering = ("learning_path", "position", "title")
    readonly_fields = ("created_at", "updated_at", "lesson_count")


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 0


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ("title", "course", "position")
    list_filter = ("course",)
    search_fields = ("title", "summary", "course__title")
    list_select_related = ("course",)
    ordering = ("course", "position", "id")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "module", "kind", "position", "estimated_minutes", "xp", "is_published")
    list_filter = ("is_published", "kind", "requires_enrollment", "course")
    search_fields = ("title", "summary")
    list_select_related = ("course", "module")
    ordering = ("course", "position", "id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    inlines = [QuizQuestionInline]
    list_display = ("lesson", "title", "passing_percent", "max_attempts", "xp", "question_count")
    list_filter = ("lesson__course",)
    search_fields = ("title", "lesson__title")
    list_select_related = ("lesson", "lesson__course")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="questions")
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("prompt_short", "quiz", "position")
    list_filter = ("quiz__lesson__course",)
    search_fields = ("prompt", "hint", "explanation")
    list_select_related = ("quiz", "quiz__lesson")
    ordering = ("quiz", "position", "id")
    readonly_fields = ("created_at", "updated_at", "correct_index")

    @admin.display(description="prompt", ordering="prompt")
    def prompt_short(self, obj):
        return obj.prompt[:60]
