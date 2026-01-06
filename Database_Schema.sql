CREATE TABLE public."User" (
	id text NOT NULL,
	email text NOT NULL,
	"password" text NULL,
	provider text NOT NULL DEFAULT 'local'::text,
	"providerAccountId" text NULL,
	"role" public."Role" NOT NULL DEFAULT 'USER'::"Role",
	"avatarUrl" text NULL,
	"emailValidated" bool NOT NULL DEFAULT false,
	"emailVerificationToken" text NULL,
	"accessToken" text NULL,
	"resetToken" text NULL,
	"resetTokenExpiry" timestamp(3) NULL,
	"createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"updatedAt" timestamp(3) NOT NULL,
	CONSTRAINT "User_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX "User_emailVerificationToken_key" ON public."User" USING btree ("emailVerificationToken");
CREATE UNIQUE INDEX "User_email_key" ON public."User" USING btree (email);

CREATE TABLE public."CandidateInterview" (
	id text NOT NULL,
	"userId" text NOT NULL,
	"mockInterviewId" text NOT NULL,
	"level" public."InterviewLevel" NULL,
	status public."CandidateInterviewStatus" NOT NULL DEFAULT 'PENDING'::"CandidateInterviewStatus",
	"recordingUrl" text NULL,
	"codeEditorSnapshot" text NULL,
	"designEditorSnapshot" text NULL,
	"videoRecording" bool NOT NULL DEFAULT false,
	"audioRecording" bool NOT NULL DEFAULT false,
	"dataUsage" bool NOT NULL DEFAULT false,
	terms bool NOT NULL DEFAULT false,
	"createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"updatedAt" timestamp(3) NOT NULL,
	CONSTRAINT "CandidateInterview_pkey" PRIMARY KEY (id),
	CONSTRAINT "CandidateInterview_mockInterviewId_fkey" FOREIGN KEY ("mockInterviewId") REFERENCES public."MockInterview"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT "CandidateInterview_userId_fkey" FOREIGN KEY ("userId") REFERENCES public."User"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX "CandidateInterview_mockInterviewId_idx" ON public."CandidateInterview" USING btree ("mockInterviewId");
CREATE INDEX "CandidateInterview_userId_idx" ON public."CandidateInterview" USING btree ("userId");


CREATE TABLE public."UserProfile" (
    id text NOT NULL,
    "userId" text NOT NULL,
    "name" text NOT NULL,
    headline text NOT NULL,
    "location" text NULL,
    "phoneNumber" text NULL,
    "linkTree" jsonb NULL,
    skills _text NULL,
    languages _text NULL,
    about text NULL,
    "companyId" text NULL,
    "jobProfileId" text NULL,
    "jobRoleId" text NULL,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    CONSTRAINT "UserProfile_pkey" PRIMARY KEY (id),
    CONSTRAINT "UserProfile_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES public."Company"(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "UserProfile_jobProfileId_fkey" FOREIGN KEY ("jobProfileId") REFERENCES public."JobProfile"(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "UserProfile_jobRoleId_fkey" FOREIGN KEY ("jobRoleId") REFERENCES public."JobRole"(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "UserProfile_userId_fkey" FOREIGN KEY ("userId") REFERENCES public."User"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE UNIQUE INDEX "UserProfile_userId_key" ON public."UserProfile" USING btree ("userId");



CREATE TABLE public."CommunityGroup" (
    id text NOT NULL,
    "name" text NOT NULL,
    slug text NOT NULL,
    description text NULL,
    "type" public."GroupType" NOT NULL,
    "imageUrl" text NULL,
    "isPrivate" bool NOT NULL DEFAULT false,
    "memberCount" int4 NOT NULL DEFAULT 0,
    tags _text NULL,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "CommunityGroup_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX "CommunityGroup_slug_key" ON public."CommunityGroup" USING btree (slug);



CREATE TABLE public."GroupPost" (
    id text NOT NULL,
    "groupId" text NOT NULL,
    "userId" text NOT NULL,
    "content" text NULL,
    "type" public."PostType" NOT NULL,
    visibility public."PostVisibility" NOT NULL,
    metadata jsonb NOT NULL,
    "mediaLinkUrl" text NULL,
    "thumbnailUrl" text NULL,
    upvotes int4 NOT NULL DEFAULT 0,
    downvotes int4 NOT NULL DEFAULT 0,
    "comments" int4 NOT NULL DEFAULT 0,
    shares int4 NOT NULL DEFAULT 0,
    "views" int4 NOT NULL DEFAULT 0,
    "isEdited" bool NOT NULL DEFAULT false,
    "isPinned" bool NOT NULL DEFAULT false,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "GroupPost_pkey" PRIMARY KEY (id),
    CONSTRAINT "GroupPost_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES public."CommunityGroup"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "GroupPost_userId_fkey" FOREIGN KEY ("userId") REFERENCES public."User"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE public."Blog" (
    id text NOT NULL,
    title text NOT NULL,
    excerpt text NOT NULL,
    "content" text NOT NULL,
    author text NOT NULL,
    "date" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image text NULL,
    slug text NOT NULL,
    tags _text NULL,
    "readTime" int4 NOT NULL DEFAULT 5,
    published bool NOT NULL DEFAULT true,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    CONSTRAINT "Blog_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX "Blog_slug_key" ON public."Blog" USING btree (slug);



CREATE TABLE public."Interview" (
    id text NOT NULL,
    "companyId" text NOT NULL,
    "userId" text NOT NULL,
    "jobRoleId" text NOT NULL,
    slug text NULL,
    title text NOT NULL,
    "location" text NULL,
    "date" timestamp(3) NOT NULL,
    difficulty public."InterviewDifficulty" NOT NULL,
    "noOfRounds" int4 NOT NULL,
    "interviewProcess" text NULL,
    "preparationSources" text NULL,
    "finalThoughts" text NULL,
    "keyTakeaways" text NULL,
    "overallRating" float8 NOT NULL,
    "isAnonymous" bool NOT NULL DEFAULT false,
    status public."InterviewStatus" NOT NULL DEFAULT 'DRAFT'::"InterviewStatus",
    "offerStatus" public."OfferStatus" NOT NULL DEFAULT 'PENDING'::"OfferStatus",
    tags _text NULL,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    "createdBy" text NOT NULL,
    "updatedBy" text NOT NULL,
    CONSTRAINT "Interview_pkey" PRIMARY KEY (id),
    CONSTRAINT "Interview_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES public."Company"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Interview_jobRoleId_fkey" FOREIGN KEY ("jobRoleId") REFERENCES public."JobRole"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Interview_userId_fkey" FOREIGN KEY ("userId") REFERENCES public."User"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX "Interview_companyId_idx" ON public."Interview" USING btree ("companyId");
CREATE INDEX "Interview_jobRoleId_idx" ON public."Interview" USING btree ("jobRoleId");
CREATE UNIQUE INDEX "Interview_slug_key" ON public."Interview" USING btree (slug);
CREATE INDEX "Interview_userId_idx" ON public."Interview" USING btree ("userId");


CREATE TABLE public."Company" (
    id text NOT NULL,
    "name" text NOT NULL,
    slug text NOT NULL,
    "logoUrl" text NULL,
    description text NOT NULL,
    "noEmployees" text NULL,
    "noOfInterviews" int4 NOT NULL DEFAULT 0,
    industry text NULL,
    website text NULL,
    "headquarterLocation" text NULL,
    rating float8 NULL,
    reviews int4 NULL,
    "isVerified" bool NOT NULL DEFAULT false,
    "linkTree" jsonb NULL,
    "foundedYear" text NULL,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    "createdBy" text NOT NULL,
    "updatedBy" text NOT NULL,
    CONSTRAINT "Company_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX "Company_slug_key" ON public."Company" USING btree (slug);



CREATE TABLE public."JobProfile" (
    id text NOT NULL,
    "name" text NOT NULL,
    description text NULL,
    slug text NOT NULL,
    "companyId" text NOT NULL,
    "isActive" bool NOT NULL DEFAULT true,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    CONSTRAINT "JobProfile_pkey" PRIMARY KEY (id),
    CONSTRAINT "JobProfile_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES public."Company"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);



CREATE TABLE public."JobRole" (
    id text NOT NULL,
    "name" text NOT NULL,
    description text NULL,
    slug text NOT NULL,
    "roleOrder" int4 NOT NULL DEFAULT 0,
    "roleStartIndex" int4 NOT NULL DEFAULT 0,
    "roleEndIndex" int4 NOT NULL DEFAULT 0,
    "roleLevel" text NOT NULL,
    "jobProfileId" text NOT NULL,
    "isActive" bool NOT NULL DEFAULT true,
    "createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp(3) NOT NULL,
    CONSTRAINT "JobRole_pkey" PRIMARY KEY (id),
    CONSTRAINT "JobRole_jobProfileId_fkey" FOREIGN KEY ("jobProfileId") REFERENCES public."JobProfile"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE public."InterviewRound" (
	id text NOT NULL,
	"interviewId" text NOT NULL,
	"name" text NOT NULL,
	duration text NULL,
	difficulty public."InterviewDifficulty" NOT NULL,
	experience text NOT NULL,
	"keyTakeaways" text NULL,
	"orderIndex" int4 NOT NULL,
	"createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"updatedAt" timestamp(3) NOT NULL,
	CONSTRAINT "InterviewRound_pkey" PRIMARY KEY (id),
	CONSTRAINT "InterviewRound_interviewId_fkey" FOREIGN KEY ("interviewId") REFERENCES public."Interview"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX "InterviewRound_interviewId_idx" ON public."InterviewRound" USING btree ("interviewId");

-- ENUMS
CREATE TYPE public."OfferStatus" AS ENUM (
	'OFFERED',
	'PENDING',
	'REJECTED');

CREATE TYPE public."InterviewDifficulty" AS ENUM (
	'EASY',
	'MEDIUM',
	'HARD');

