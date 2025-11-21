import { HeroGeometric } from '../components/ui/shape-landing-hero';

export default function LandingPage() {
    const isLoggedIn = !!localStorage.getItem('token');

    return (
        <HeroGeometric
            badge="AI Sales Agent"
            title1="Supercharge Your"
            title2="B2B Sales Pipeline"
            isLoggedIn={isLoggedIn}
        />
    );
}
