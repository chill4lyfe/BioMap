import { useState } from 'react';
import {
  ArrowRight,
  Dna,
  LockKeyhole,
  Mail,
  UserRound,
} from 'lucide-react';

import { supabase } from '../../lib/supabaseClient';

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const isSignup = mode === 'signup';

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setMessage('');
    setError('');

    if (!email || !password) {
      setError('Email and password are required.');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      setLoading(false);
      return;
    }

    try {
      if (isSignup) {
        const { error: signupError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              full_name: name,
              role: 'researcher',
            },
          },
        });

        if (signupError) throw signupError;

        setMessage(
          'Account created. If email confirmation is enabled, verify your email before login.'
        );
        setMode('login');
      } else {
        const { error: loginError } =
          await supabase.auth.signInWithPassword({
            email,
            password,
          });

        if (loginError) throw loginError;
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Authentication failed.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-[#02050b] text-slate-200">
      <section className="hidden w-[46%] border-r border-slate-800/80 bg-[#070b14] p-10 lg:flex lg:flex-col lg:justify-between">
        <div>
          <div className="mb-12 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Dna size={22} className="text-blue-400" />
            </div>

            <div>
              <h1 className="font-display text-2xl tracking-wider text-white">
                BIOMAP
              </h1>
              <p className="text-[9px] uppercase tracking-[0.22em] text-slate-600">
                Cellular Intelligence
              </p>
            </div>
          </div>

          <div className="max-w-xl">
            <div className="section-kicker mb-4">
              Researcher access
            </div>
            <h2 className="font-display text-5xl leading-tight tracking-wide text-white">
              Secure workspace for cell analysis.
            </h2>
            <p className="mt-5 text-sm leading-7 text-slate-500">
              Sign in to open the BioMap research dashboard, manage datasets,
              and continue into the existing segmentation, tracking, and lineage
              analysis workspace.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
            {[
                { label: 'Datasets', status: 'Ready' },
                { label: 'Engine', status: 'Loaded' },
                { label: 'Lineage', status: 'Ready' },
            ].map((item) => (
                <div key={item.label} className="panel p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-600">
                    {item.label}
                </p>
                <p className="mt-2 text-sm text-blue-300">{item.status}</p>
                </div>
            ))}
            </div>
      </section>

      <main className="flex flex-1 items-center justify-center px-5 py-10">
        <div className="w-full max-w-md">
          <div className="mb-7 lg:hidden">
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Dna size={22} className="text-blue-400" />
            </div>
            <h1 className="font-display text-2xl tracking-wider text-white">
              BIOMAP
            </h1>
          </div>

          <div className="panel p-6">
            <div className="mb-6">
              <div className="section-kicker mb-3">
                {isSignup ? 'Create account' : 'Welcome back'}
              </div>
              <h2 className="font-display text-3xl tracking-wide text-white">
                {isSignup ? 'Sign up' : 'Login'}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {isSignup
                  ? 'Create a researcher account for BioMap.'
                  : 'Login to continue to your research dashboard.'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignup && (
                <label className="block">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                    Researcher name
                  </span>
                  <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#050914] px-3 py-3">
                    <UserRound size={16} className="text-slate-500" />
                    <input
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Enter Your Name"
                      className="w-full bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-700"
                    />
                  </div>
                </label>
              )}

              <label className="block">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                  Email
                </span>
                <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#050914] px-3 py-3">
                  <Mail size={16} className="text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="researcher@lab.com"
                    className="w-full bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-700"
                  />
                </div>
              </label>

              <label className="block">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                  Password
                </span>
                <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#050914] px-3 py-3">
                  <LockKeyhole size={16} className="text-slate-500" />
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Minimum 6 characters"
                    className="w-full bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-700"
                  />
                </div>
              </label>

              {error && (
                <div className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-xs text-red-300">
                  {error}
                </div>
              )}

              {message && (
                <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-2 text-xs text-emerald-300">
                  {message}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-3 text-xs font-semibold uppercase tracking-wider text-white shadow-[0_0_25px_rgba(37,99,235,.18)] transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading
                  ? 'Please wait'
                  : isSignup
                    ? 'Create account'
                    : 'Login'}
                <ArrowRight size={15} />
              </button>
            </form>

            <button
              type="button"
              onClick={() => {
                setMode(isSignup ? 'login' : 'signup');
                setError('');
                setMessage('');
              }}
              className="mt-5 w-full text-center text-sm text-slate-500 transition hover:text-blue-300"
            >
              {isSignup
                ? 'Already have an account? Login'
                : "Don't have an account? Sign up"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}