// CandidateCard placeholder
interface Props {
  name: string;
  email: string;
}

export default function CandidateCard({ name, email }: Props) {
  return (
    <div>
      <p>{name}</p>
      <p>{email}</p>
    </div>
  );
}
