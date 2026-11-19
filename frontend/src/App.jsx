import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { useAuth } from "./context/AuthContext";
import PublicLayout from "./layouts/PublicLayout";
import AppLayout from "./layouts/AppLayout";
import { Loading } from "./components/ui";

const Home = lazy(() => import("./pages/public/Home"));
const About = lazy(() => import("./pages/public/About"));
const Catalog = lazy(() => import("./pages/learning/Catalog"));
const CourseDetail = lazy(() => import("./pages/learning/CourseDetail"));
const LessonPlayer = lazy(() => import("./pages/learning/LessonPlayer"));
const Certificates = lazy(() => import("./pages/learning/Certificates"));
const Challenges = lazy(() => import("./pages/challenges/Challenges"));
const ChallengeWorkspace = lazy(() => import("./pages/challenges/ChallengeWorkspace"));
const Community = lazy(() => import("./pages/community/Community"));
const PostDetail = lazy(() => import("./pages/community/PostDetail"));
const Projects = lazy(() => import("./pages/community/Projects"));
const ProjectDetail = lazy(() => import("./pages/community/ProjectDetail"));
const ProjectEditor = lazy(() => import("./pages/community/ProjectEditor"));
const Mentorship = lazy(() => import("./pages/mentorship/Mentorship"));
const MentorDetail = lazy(() => import("./pages/mentorship/MentorDetail"));
const MyMentorships = lazy(() => import("./pages/mentorship/MyMentorships"));
const Dashboard = lazy(() => import("./pages/app/Dashboard"));
const Achievements = lazy(() => import("./pages/app/Achievements"));
const Notifications = lazy(() => import("./pages/app/Notifications"));
const ProfileEdit = lazy(() => import("./pages/app/ProfileEdit"));
const MemberProfile = lazy(() => import("./pages/app/MemberProfile"));
const SignIn = lazy(() => import("./pages/auth/SignIn"));
const SignUp = lazy(() => import("./pages/auth/SignUp"));
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/auth/ResetPassword"));
const AdminLayout = lazy(() => import("./pages/admin/AdminLayout"));
const NotFound = lazy(() => import("./pages/NotFound"));

function Protected({ children, role }) {
  const { isAuthenticated, isBooting, isAdmin, isMentor } = useAuth();
  const location = useLocation();

  if (isBooting) {
    return (
      <div style={{ minHeight: "60vh", display: "grid", placeItems: "center" }}>
        <Loading label="Checking your session" />
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location.pathname + location.search }} replace />;
  }
  if (role === "admin" && !isAdmin) return <Navigate to="/dashboard" replace />;
  if (role === "mentor" && !isMentor && !isAdmin) return <Navigate to="/mentorship" replace />;
  return children;
}

function Centered({ children }) {
  return (
    <Suspense
      fallback={
        <div style={{ minHeight: "60vh", display: "grid", placeItems: "center" }}>
          <Loading label="Loading" />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <Centered>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Public marketing + browse pages */}
          <Route element={<PublicLayout />}>
            <Route index element={<Home />} />
            <Route path="about" element={<About />} />
            <Route path="signin" element={<SignIn />} />
            <Route path="signup" element={<SignUp />} />
            <Route path="forgot-password" element={<ForgotPassword />} />
            <Route path="reset-password" element={<ResetPassword />} />
            <Route path="learning" element={<Catalog />} />
            <Route path="learning/:slug" element={<CourseDetail />} />
            <Route path="courses" element={<Navigate to="/learning" replace />} />
            <Route path="courses/*" element={<Navigate to="/learning" replace />} />
            <Route path="challenges" element={<Challenges />} />
            <Route path="challenges/:id" element={<ChallengeWorkspace />} />
            <Route path="community" element={<Community />} />
            <Route path="community/posts/:id" element={<PostDetail />} />
            <Route path="community/projects" element={<Projects />} />
            <Route path="community/projects/:id" element={<ProjectDetail />} />
            <Route path="mentorship" element={<Mentorship />} />
            <Route path="mentorship/:id" element={<MentorDetail />} />
            <Route path="members/:id" element={<MemberProfile />} />
            <Route path="*" element={<NotFound />} />
          </Route>

          {/* Signed-in product surface */}
          <Route element={<AppLayout />}>
            <Route
              path="dashboard"
              element={
                <Protected>
                  <Dashboard />
                </Protected>
              }
            />
            <Route
              path="learning/:courseId/lessons/:lessonId"
              element={
                <Protected>
                  <LessonPlayer />
                </Protected>
              }
            />
            <Route
              path="certificates"
              element={
                <Protected>
                  <Certificates />
                </Protected>
              }
            />
            <Route
              path="projects/new"
              element={
                <Protected>
                  <ProjectEditor />
                </Protected>
              }
            />
            <Route
              path="projects/:id/edit"
              element={
                <Protected>
                  <ProjectEditor />
                </Protected>
              }
            />
            <Route
              path="achievements"
              element={
                <Protected>
                  <Achievements />
                </Protected>
              }
            />
            <Route
              path="notifications"
              element={
                <Protected>
                  <Notifications />
                </Protected>
              }
            />
            <Route
              path="profile"
              element={
                <Protected>
                  <ProfileEdit />
                </Protected>
              }
            />
            <Route
              path="mentorships"
              element={
                <Protected>
                  <MyMentorships />
                </Protected>
              }
            />
          </Route>

          {/* Admin */}
          <Route
            path="admin/*"
            element={
              <Protected role="admin">
                <AdminLayout />
              </Protected>
            }
          />
        </Routes>
      </AnimatePresence>
    </Centered>
  );
}
